from fastmcp import FastMCP
import json

mcp = FastMCP("COOL MCP")

# ---------------- PLAY SONG ----------------
@mcp.tool()
def PLAY_SONG() -> str:
    play = {
        "version": "0.0.1",
        "header": {
            "source": "AI-SoC",
            "destination": "DCU-IVI",
            "msg_type": "Request",
            "ack_required": "Yes"
        },
        "request": {
            "service_name": "PlaySong",
            "parameters": {
                "genre": "jazz",
                "song_title": "recovery",
                "type": "PLAY"
            }
        }
    }

    



    return json.dumps({
        "event_udp": play,
        "user_response": f"Playing song for you."
    })


# ---------------- AMBIENT LIGHT ----------------
@mcp.tool()
def set_ambient_light(ambient_light_colour_RGB: str = None, turn_off: bool = False) -> str:
    msg = "Ambient light turned off" if turn_off else f"Ambient light set to RGB({ambient_light_colour_RGB})"


    return json.dumps({
        "event_udp": None,
        "user_response": msg
    })



# ---------------- DESTINATION ----------------
@mcp.tool()
def change_destination(to: str) -> str:

    return json.dumps({
        "event_udp": None,
        "user_response": f"Navigation destination changed to {to}"
    })


# ---------------- CALL CONTACT ----------------
@mcp.tool()
def CALL_CONTACT() -> str:
    call = {
        "version": "0.0.1",
        "header": {
            "source": "AI-SoC",
            "destination": "DCU-IVI",
            "msg_type": "Request",
            "ack_required": "true"
        },
        "request": {
            "service_name": "PhoneCall",
            "parameters": {
                "phone_number": "7816070229",
                "phone_contact": "Bharath"
            }
        }
    }


    return json.dumps({
        "event_udp": call,
        "user_response": f"Calling Bharath for you."
    })
    
    
    




if __name__ == "__main__":
    mcp.run(transport="stdio")

