from __future__ import annotations

import json
import secrets
import urllib.parse
from pathlib import Path
from typing import Dict, Any

import mcp.types as types
from fastapi import FastAPI, Form, HTTPException, Request
from fastmcp import FastMCP
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates

#from oidc_auth_server import auth_codes

# Initialize FastMCP with HTTP streaming
mcp = FastMCP(
    name="first-app-mcp",
    stateless_http=True,
)



STATIC_DIR = Path(__file__).parent / "static"
FIRST_CSS = (STATIC_DIR / "first-app.css").read_text()
FIRST_JS = (STATIC_DIR / "first-app.js").read_text()
templates = Jinja2Templates(directory="templates")

# === UI HTML that ChatGPT renders as a component ===
def get_first_app_html():
    return f"""<div id="first-app-root"></div>
    <style>{FIRST_CSS}</style>
    <script type="module">{FIRST_JS}</script>"""


MIME_TYPE = "text/html+skybridge"
TEMPLATE_URI = "ui://widget/firstapp.html"



def make_unauthorized_result() -> types.ServerResult:
    """Return a properly typed 401-equivalent result for MCP."""
    return types.ServerResult(
        type="result",
        status="error",
        error=types.ErrorData(
            code=401,
            message="Access token expired or invalid. Please reauthorize the connector."
        )
    )

def _make_unauthorized_result() -> types.ServerResult:
    return types.ServerResult(
        type="result",
        status="error",
        error=types.ErrorData(
            code=401,
            message="unauthorized"  # short keyword recognized by ChatGPT
        )
    )
def _embedded_widget_resource():
    """Create embedded widget resource for ChatGPT UI rendering."""
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=TEMPLATE_URI,
            mimeType=MIME_TYPE,
            text=get_first_app_html(),
            title="First App",
        ),
    )

@mcp.tool()
def get_recommendations(city: str,state: str, cuisine: str) -> Dict[str, Any]:
    """
    Retrieves Restaurant recommendations as a JSON object.

    Args:
        city: city for which to retrieve recommendations.
        state: state for which to retrieve recommendations.
        cuisine: cuisine for which to retrieve recommendations.

    Returns:
        A dictionary containing the restaurant name, description, cuisine, $$, rating, image, city and state.
    """
    # Simulate fetching data
    RESTAURANTS = [
        {
            "name": "Pizzeria Bianca",
            "description": "Neapolitan-style pies from a wood-fired oven.",
            "cuisine": "Italian",
            "$$": "$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1541745537413-b804b0c5fbbf",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Desert Ramen Bar",
            "description": "Slow-simmered broths and hand-pulled noodles.",
            "cuisine": "Japanese",
            "$$": "$$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1557872943-16a5ac26437b",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Sonoran Grill",
            "description": "Mesquite-grilled carne asada and street tacos.",
            "cuisine": "Mexican",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1552332386-f8dd00dc2f85",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Cactus & Curry",
            "description": "Modern Indian flavors with Southwest touches.",
            "cuisine": "Indian",
            "$$": "$$",
            "rating": 4.4,
            "image": "https://images.unsplash.com/photo-1604908554007-1d064f7a97a3",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Bayview Oyster House",
            "description": "Raw bar, chowders, and coastal classics.",
            "cuisine": "Seafood",
            "$$": "$$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1553621042-f6e147245754",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Mission Taquería",
            "description": "Al pastor cut to order with house-made salsas.",
            "cuisine": "Mexican",
            "$$": "$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1541866741-4b1c1f7d2f2a",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Little Sichuan",
            "description": "Chongqing spicy noodles and peppercorn specialties.",
            "cuisine": "Chinese",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1554995207-c18c203602cb",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Trattoria del Mare",
            "description": "Homemade pasta and coastal Italian plates.",
            "cuisine": "Italian",
            "$$": "$$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1521389508051-d7ffb5dc8bbf",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Brooklyn Slice Co.",
            "description": "Thin-crust pies with classic NYC toppings.",
            "cuisine": "Italian",
            "$$": "$",
            "rating": 4.3,
            "image": "https://images.unsplash.com/photo-1548365328-9f547fb0953c",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Hanami Izakaya",
            "description": "Yakitori, sashimi, and sake flights.",
            "cuisine": "Japanese",
            "$$": "$$$",
            "rating": 4.8,
            "image": "https://images.unsplash.com/photo-1553621042-2f9b6f0b7d3a",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Hanami Izakaya",
            "description": "Yakitor, sashim",
            "cuisine": "Japanese",
            "$$": "$",
            "rating": 4.1,
            "image": "https://images.unsplash.com/photo-1553621042-2f9b6f0b7d3a",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Bombay Junction",
            "description": "Regional Indian thalis and tandoori specialties.",
            "cuisine": "Indian",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d0",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Taco Alley",
            "description": "Birria tacos and consomé, made daily.",
            "cuisine": "Mexican",
            "$$": "$",
            "rating": 4.4,
            "image": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b",
            "city": "Austin",
            "state": "TX",
        },
        {
            "name": "Hill Country Smokehouse",
            "description": "Offset-smoked brisket and ribs by the pound.",
            "cuisine": "Barbecue",
            "$$": "$$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1552332386-9c6a7a44d6cf",
            "city": "Austin",
            "state": "TX",
        },
        {
            "name": "Uptown Bistro",
            "description": "Seasonal New American with local produce.",
            "cuisine": "American",
            "$$": "$$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0",
            "city": "Chicago",
            "state": "IL",
        },
        {
            "name": "Kimchi Corner",
            "description": "Korean BBQ and bubbling stews.",
            "cuisine": "Korean",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1544025162-d76694265947",
            "city": "Chicago",
            "state": "IL",
        },
    ]

    results = []
    for rest in RESTAURANTS:
        if rest["city"] == city and rest["state"] == state and rest["cuisine"] == cuisine:
            results.append(rest)

    structured_content = {
        "restaurants": []
    }

    for r in results:
        structured_content["restaurants"].append({
            "name": r["name"],
            "description": r["description"],
            "cuisine": r["cuisine"],
            "price_range": r["$$"],
            "rating": r["rating"],
            "image": r["image"]
        })

    return structured_content


# Override call_tool handler to use the working pattern
async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:

    if req.params.name != "first_app_tool":
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}"
                    )
                ],
                isError=True,
            )
        )
    print(req.params.name)

    arguments = req.params.arguments or {}
    cuisine = arguments.get("cuisine", "Japanese")
    city = arguments.get("city", "New York")
    state = arguments.get("state", "NY")

    print(f"Cuisine is {cuisine}")
    print(f"City is {city}")
    print(f"State is {state}")

    RESTAURANTS = [
        {
            "name": "Pizzeria Bianca",
            "description": "Neapolitan-style pies from a wood-fired oven.",
            "cuisine": "Italian",
            "$$": "$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1541745537413-b804b0c5fbbf",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Desert Ramen Bar",
            "description": "Slow-simmered broths and hand-pulled noodles.",
            "cuisine": "Japanese",
            "$$": "$$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1557872943-16a5ac26437b",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Sonoran Grill",
            "description": "Mesquite-grilled carne asada and street tacos.",
            "cuisine": "Mexican",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1552332386-f8dd00dc2f85",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Cactus & Curry",
            "description": "Modern Indian flavors with Southwest touches.",
            "cuisine": "Indian",
            "$$": "$$",
            "rating": 4.4,
            "image": "https://images.unsplash.com/photo-1604908554007-1d064f7a97a3",
            "city": "Phoenix",
            "state": "AZ",
        },
        {
            "name": "Bayview Oyster House",
            "description": "Raw bar, chowders, and coastal classics.",
            "cuisine": "Seafood",
            "$$": "$$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1553621042-f6e147245754",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Mission Taquería",
            "description": "Al pastor cut to order with house-made salsas.",
            "cuisine": "Mexican",
            "$$": "$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1541866741-4b1c1f7d2f2a",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Little Sichuan",
            "description": "Chongqing spicy noodles and peppercorn specialties.",
            "cuisine": "Chinese",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1554995207-c18c203602cb",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Trattoria del Mare",
            "description": "Homemade pasta and coastal Italian plates.",
            "cuisine": "Italian",
            "$$": "$$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1521389508051-d7ffb5dc8bbf",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Brooklyn Slice Co.",
            "description": "Thin-crust pies with classic NYC toppings.",
            "cuisine": "Italian",
            "$$": "$",
            "rating": 4.3,
            "image": "https://images.unsplash.com/photo-1548365328-9f547fb0953c",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Hanami Izakaya",
            "description": "Yakitori, sashimi, and sake flights.",
            "cuisine": "Japanese",
            "$$": "$$$",
            "rating": 4.8,
            "image": "https://images.unsplash.com/photo-1553621042-2f9b6f0b7d3a",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Hanami Izakaya",
            "description": "Yakitor, sashim",
            "cuisine": "Japanese",
            "$$": "$",
            "rating": 4.1,
            "image": "https://images.unsplash.com/photo-1553621042-2f9b6f0b7d3a",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Bombay Junction",
            "description": "Regional Indian thalis and tandoori specialties.",
            "cuisine": "Indian",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d0",
            "city": "New York",
            "state": "NY",
        },
        {
            "name": "Taco Alley",
            "description": "Birria tacos and consomé, made daily.",
            "cuisine": "Mexican",
            "$$": "$",
            "rating": 4.4,
            "image": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b",
            "city": "Austin",
            "state": "TX",
        },
        {
            "name": "Hill Country Smokehouse",
            "description": "Offset-smoked brisket and ribs by the pound.",
            "cuisine": "Barbecue",
            "$$": "$$",
            "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1552332386-9c6a7a44d6cf",
            "city": "Austin",
            "state": "TX",
        },
        {
            "name": "Uptown Bistro",
            "description": "Seasonal New American with local produce.",
            "cuisine": "American",
            "$$": "$$$",
            "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0",
            "city": "Chicago",
            "state": "IL",
        },
        {
            "name": "Kimchi Corner",
            "description": "Korean BBQ and bubbling stews.",
            "cuisine": "Korean",
            "$$": "$$",
            "rating": 4.5,
            "image": "https://images.unsplash.com/photo-1544025162-d76694265947",
            "city": "Chicago",
            "state": "IL",
        },
    ]

    results = []
    for rest in RESTAURANTS:
        if rest["city"] == city and rest["state"] == state and rest["cuisine"] == cuisine:
            results.append(rest)

    structured_content = {
        "restaurants": []
    }

    for r in results:
        structured_content["restaurants"].append({
            "name": r["name"],
            "description": r["description"],
            "cuisine": r["cuisine"],
            "price_range": r["$$"],
            "rating": r["rating"],
            "image": r["image"]
        })

    print(json.dumps(structured_content, indent=2))

    # Create embedded widget resource for ChatGPT integration
    widget_resource = _embedded_widget_resource()

    # Build metadata with embedded widget for UI rendering
    meta = {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        "openai/outputTemplate": TEMPLATE_URI,
        "openai/toolInvocation/invoking": "Running FirstApp",
        "openai/toolInvocation/invoked": "Completed FirstApp",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

    # Return result with structured content (following working example pattern)
    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text="FirstApp Tool execution completed",
                )
            ],
            structuredContent=structured_content,  # This is the key data for the UI
            _meta=meta,
        )
    )



# === Custom _list_tools handler ===
@mcp._mcp_server.list_tools()
async def list_tools(context):
    """Handles the ListToolsRequest from MCP clients (like ChatGPT)."""
    print("🧭 Handling tools/list request...")

    # Build the MCP-compatible tool list
    tools = [
        types.Tool(
            name="first_app_tool",
            title="FirstApp Tool",
            description="FirstApp",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City"},
                    "state": {"type": "string", "description": "State"},
                    "cuisine": {"type": "string", "description": "Preferred cuisine"}
                },
                "required": ["city", "state", "cuisine"],
            }
        )
    ]

    # Return in MCP protocol format
    return types.ListToolsResult(tools=tools)



# Register the tool following the working pattern
@mcp._mcp_server.list_tools()
async def _list_tools(req: types.ListToolsRequest) -> list[types.Tool]:
    return [
        types.Tool(
            name="first_app_tool",
            title="FirstApp Tool",
            description="FirstApp",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City"},
                    "state": {"type": "string", "description": "State"},
                    "cuisine": {"type": "string", "description": "Preferred cuisine"}
                },
                "required": ["city", "state", "cuisine"],
            },
            _meta={
                "openai/outputTemplate": TEMPLATE_URI,
                "openai/toolInvocation/invoking": "Running FirstApp",
                "openai/toolInvocation/invoked": "Completed FirstApp",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
            securitySchemes=[
                    {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "authorization_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                "token_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                "registration_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/register",
                                "authorizationUrl": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                "tokenUrl": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                "scopes": {
                                    "token": "token"
                                }
                            }
                        }
                    }]
        )
    ]





# Override list_resources to register UI components like working example
@mcp._mcp_server.list_resources()
async def _list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            name="FirstApp",
            title="FirstApp",
            uri=TEMPLATE_URI,
            description="FirstApp widget markup",
            mimeType=MIME_TYPE,
            _meta={
                "openai/outputTemplate": TEMPLATE_URI,
                "openai/toolInvocation/invoking": "Running FirstApp",
                "openai/toolInvocation/invoked": "Completed FirstApp",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
            securitySchemes=[{"type": "noauth"},
                             {
                                 "type": "oauth2",
                                 "flows": {
                                     "authorizationCode": {
                                         "authorization_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                         "token_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                         "registration_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/register",
                                         "authorizationUrl": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                         "tokenUrl": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                         "scopes": {
                                             "token": "token"
                                         }
                                     }
                                 }
                             }]
        ),
        types.Resource(
            uri="resource://mcp/tools/call",
            name="Tool Invocation",
            mimeType=MIME_TYPE,
            securitySchemes=[{"type": "noauth"},
                             {
                                 "type": "oauth2",
                                 "flows": {
                                     "authorizationCode": {
                                         "authorization_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                         "token_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                         "registration_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/register",
                                         "authorizationUrl": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                         "tokenUrl": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                         "scopes": {
                                             "token": "token"
                                         }
                                     }
                                 }
                             }]
        )
    ]


# Override read_resource handler to serve UI components like working example
async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    if str(req.params.uri) != TEMPLATE_URI:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=TEMPLATE_URI,
            mimeType=MIME_TYPE,
            text=get_first_app_html(),
            _meta={
                "openai/outputTemplate": TEMPLATE_URI,
                "openai/toolInvocation/invoking": "Running FirstApp",
                "openai/toolInvocation/invoked": "Completed FirstApp",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
            },
            securitySchemes=[{"type": "noauth"},
                             {
                                 "type": "oauth2",
                                 "flows": {
                                     "authorizationCode": {
                                         "authorization_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                         "token_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                         "registration_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/register",
                                         "authorizationUrl": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
                                         "tokenUrl": "https://0c819c023f82.ngrok-free.app/oauth2/token",
                                         "scopes": {
                                             "token": "token"
                                         }
                                     }
                                 }
                             }]
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


# Register the handlers like working example
mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource
#mcp._mcp_server.request_handlers[types.ListToolsRequest] = list_tools


# Create the streamable HTTP app following the working pattern
app = mcp.streamable_http_app()

rest_api = FastAPI()

@rest_api.get("/oauth2/authorize", response_class=HTMLResponse)
async def authorize(
    request: Request,
    client_id: str,
    redirect_uri: str,
    state: str,
    response_type: str = "code",
):
    """Displays login page when the user visits /oauth2/authorize."""

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "client_id": client_id, "redirect_uri": redirect_uri, "state": state},
    )



@rest_api.get("/health")
async def healthz():
    return {"status": "ok"}


@rest_api.get("/.well-known/openid-configuration")
async def openid_configuration():
    config = {
        "issuer": "https://0c819c023f82.ngrok-free.app",
        "authorization_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
        "token_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/token",
        "registration_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        #"grant_types_supported": ["client_credentials"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
        #"scopes_supported": ["openid", "profile", "email", "token"],
        "scopes_supported": ["token"],
        "claims_supported": ["sub", "api_token"]
    }
    return config

@rest_api.get("/.well-known/oauth-authorization-server")
async def openid_auth_configuration():
    config = {
        "issuer": "https://0c819c023f82.ngrok-free.app",
        "authorization_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/authorize",
        "token_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/token",
        "registration_endpoint": "https://0c819c023f82.ngrok-free.app/oauth2/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        #"grant_types_supported": ["client_credentials"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
        #"scopes_supported": ["openid", "profile", "email", "token"],
        "scopes_supported": ["token"],
        "claims_supported": ["sub", "api_token"]
    }
    return config


@rest_api.post("/oauth2/register")
async def oauth_register():
    """
 Handles the dynamic client registration request from ChatGPT.
 We can just return a static response.
 """
    # In a real app, you might inspect request.json['redirect_uris']
    # but for this purpose, a static response is fine.


    response = {
        "client_id": "chatgpt-test-connector-client",
        "redirect_uris": [
        "https://chatgpt.com/connector_platform_oauth_redirect"
        ],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "application_type": "web"
}
    return response

@rest_api.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(...),
):
    """Step 2: User posts credentials."""
    # ⚠️ Demo authentication logic — replace with real check
    if username != "test" or password != "testadmin":
        raise HTTPException(401, "invalid credentials")

    # Generate one-time authorization code
    code = secrets.token_urlsafe(16)
    #auth_codes[code] = {"client_id": client_id, "username": username}

    # Redirect back to ChatGPT callback (or RP redirect_uri)
    redirect_url = f"{redirect_uri}?code={code}&state={urllib.parse.quote(state)}"
    return RedirectResponse(url=redirect_url, status_code=302)


@rest_api.post("/oauth2/token")
async def oauth_token(request: Request):
    # Extract data from the form-encoded request

    form_data = await request.form()
    grant_type = form_data.get("grant_type")
    code = form_data.get("code")
    client_id = form_data.get("client_id")
    code_verifier = form_data.get("code_verifier")
    refresh_token = form_data.get("refresh_token")
    scope = "token"
    if grant_type == "authorization_code":

        # Return the API key as the 'access_token'
        access_token = secrets.token_urlsafe(32)
        new_refresh_token = secrets.token_urlsafe(32)
        token_response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 600,  # 90 days (or however long you want)
            "refresh_token": new_refresh_token,
            #"expires_in": 600,
            "scope": scope
        }
        print("response :", token_response)

        return token_response
    elif grant_type == "refresh_token":
        new_token = secrets.token_urlsafe(32)
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "refresh_token": refresh_token,  # can rotate or reuse
            "scope": scope,
        }
    else:
        raise HTTPException(400, "unsupported grant_type")

# ----------------------------------------------------
# TODO: YOUR CUSTOM LOGIC GOES HERE
#
# 1. Validate the 'code' and optionally the 'code_verifier' (PKCE).
# 2. Find the user_id associated with this validated 'code'.
# 3. Look up that user's permanent API key from your database.
#
# user_api_key = my_db.get_api_key(user_id)
#
# ----------------------------------------------------

# For this example, we'll just hardcode it.
    scope = "token"
    # Return the API key as the 'access_token'
    access_token = secrets.token_urlsafe(32)
    token_response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 7776000,  # 90 days (or however long you want)
        "scope": scope
    }
    print("response :", token_response)

    return token_response


app.mount("/", rest_api)

# Create the streamable HTTP app following the working pattern
#fast_app.mount("/mcp", app=app)

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8006))

    print("=" * 60)
    print("MCP Server")
    print("=" * 60)
    print(f"\nEndpoints:")
    print(f"  MCP:    http://0.0.0.0:{port}/mcp")
    print(f"  Health: http://0.0.0.0:{port}/health")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
