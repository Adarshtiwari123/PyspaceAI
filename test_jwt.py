import base64
import json
import sys

def decode_jwt(jwt_string):
    """
    Decodes the payload of a JWT string and prints the contained data.
    Works for both the authentication token and the giant session_id JWT.
    """
    try:
        # A JWT has 3 parts separated by dots: header.payload.signature
        if "." not in jwt_string:
            print("❌ Error: Not a valid JWT string (missing dots).")
            return

        # Extract the middle part (the payload)
        payload_b64 = jwt_string.split(".")[1]
        
        # Add necessary padding for base64 decoding
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        
        # Decode the base64 string to JSON
        payload_json = base64.urlsafe_b64decode(payload_b64).decode("utf-8")
        
        # Parse the JSON string into a Python dictionary
        payload = json.loads(payload_json)
        
        print("\n✅ Successfully decoded JWT payload:\n")
        print(json.dumps(payload, indent=4))
        
        # Show specific common fields if they exist
        print("\n--- Key Information Extracted ---")
        if "userid" in payload:
            print(f"👤 User ID: {payload['userid']}")
        if "session_id" in payload:
            print(f"🆔 Session ID: {payload['session_id']}")
        if "duration_minutes" in payload:
            print(f"⏱️ Duration: {payload['duration_minutes']} minutes")
        if "sub" in payload:
            print(f"📧 Subject (User): {payload['sub']}")
            
        print("---------------------------------")
        
    except Exception as e:
        print(f"❌ Failed to decode JWT: {str(e)}")

if __name__ == "__main__":
    print("=== JWT Decoder Test Script ===")
    
    # You can paste your JWT string here to test it directly
    test_token = input("Paste your JWT token or session_id here to test: ").strip()
    
    if test_token:
        decode_jwt(test_token)
    else:
        print("No token provided. Exiting.")
