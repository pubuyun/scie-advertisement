from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import io
import traceback
from fetchinfo import cmsFetcher
from find_adv import calculate_subject_decisions, process_subjects

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=[
        "session-token",
        "requires-captcha",
    ],  # Allow frontend to read session-token header
)

# Store user session information
user_sessions = {}


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        fetcher = cmsFetcher(username, password)
        needs_captcha, result = fetcher.login()

        # Save fetcher instance to session
        session_token = username  # Using username as session token for simplicity
        user_sessions[session_token] = fetcher

        if needs_captcha:
            # Return captcha image
            return StreamingResponse(
                io.BytesIO(result),
                media_type="image/png",
                headers={
                    "session-token": session_token,
                    "Access-Control-Expose-Headers": "session-token",
                    "requires-captcha": "true",
                },
            )
        else:
            # Direct login successful
            if result:
                response = JSONResponse(
                    {
                        "status": "success",
                        "auth_token": session_token,
                        "requires_captcha": False,
                        "message": "Login successful",
                    }
                )
                response.headers["session-token"] = session_token
                response.headers["Access-Control-Expose-Headers"] = "session-token"
                return response
            else:
                raise HTTPException(
                    status_code=401, detail="Login failed: Invalid credentials"
                )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth")
async def auth(session_token: str = Form(...), captcha: str = Form(...)):
    try:
        if session_token not in user_sessions:
            print(f"Session token {session_token} not found in sessions")
            print(f"Available sessions: {list(user_sessions.keys())}")
            raise HTTPException(status_code=401, detail="Invalid session")

        fetcher = user_sessions[session_token]
        fetcher.set_safecode(captcha)

        if not fetcher.auth():
            raise HTTPException(
                status_code=401,
                detail="Authentication failed: Wrong captcha or session expired",
            )

        # Authentication successful, return auth token (using session token as auth token)
        return JSONResponse(
            {
                "status": "success",
                "auth_token": session_token,
                "message": "Authentication successful",
            }
        )

    except HTTPException as e:
        traceback.print_exc()
        print(f"HTTP Exception: {str(e)}")
        raise e
    except Exception as e:
        traceback.print_exc()
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/image")
async def get_image(auth_token: str):
    try:
        if auth_token not in user_sessions:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        fetcher = user_sessions[auth_token]

        # Get scores and referrals
        if not (fetcher.fetch_score() and fetcher.fetch_referrals()):
            raise HTTPException(status_code=500, detail="Failed to fetch data")

        scores = fetcher.get_scores()
        referrals = fetcher.get_referrals()

        # Process data to get recommended image
        decisions = calculate_subject_decisions(scores, referrals)
        result = process_subjects(decisions)

        if not result:
            raise HTTPException(
                status_code=500, detail="Failed to get recommended image"
            )

        return JSONResponse(result)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
