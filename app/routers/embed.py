from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from app.config import Config

router = APIRouter(prefix="/embed", tags=["embed"])


@router.get("/code/{bot_id}")
async def get_embed_code(bot_id: str):
    """Generate embed code for a bot"""

    iframe_code = f'''<!-- Chatbot iframe -->
<iframe 
    src="{Config.APP_URL}/widget/chat/{bot_id}"
    style="width: 100%; height: 600px; border: none; border-radius: 10px;"
    frameborder="0"
    allow="microphone">
</iframe>'''

    script_code = f'''<!-- Chatbot Widget -->
<script>
(function() {{
    var botId = "{bot_id}";
    var script = document.currentScript;
    
    // Create widget container
    var widget = document.createElement('div');
    widget.id = 'chatbot-widget-' + botId;
    widget.style.position = 'fixed';
    widget.style.bottom = '20px';
    widget.style.right = '20px';
    widget.style.zIndex = '999999';
    
    // Create chat button
    var button = document.createElement('button');
    button.innerHTML = '💬';
    button.style.width = '60px';
    button.style.height = '60px';
    button.style.borderRadius = '50%';
    button.style.backgroundColor = '#3B82F6';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.cursor = 'pointer';
    button.style.fontSize = '24px';
    button.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    
    // Create iframe container (hidden by default)
    var chatContainer = document.createElement('div');
    chatContainer.id = 'chatbot-iframe-' + botId;
    chatContainer.style.display = 'none';
    chatContainer.style.position = 'fixed';
    chatContainer.style.bottom = '90px';
    chatContainer.style.right = '20px';
    chatContainer.style.width = '350px';
    chatContainer.style.height = '500px';
    chatContainer.style.borderRadius = '10px';
    chatContainer.style.overflow = 'hidden';
    chatContainer.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    
    var iframe = document.createElement('iframe');
    iframe.src = '{Config.APP_URL}/widget/chat/' + botId;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    
    chatContainer.appendChild(iframe);
    
    // Toggle chat on button click
    button.onclick = function() {{
        if (chatContainer.style.display === 'none') {{
            chatContainer.style.display = 'block';
            button.innerHTML = '✕';
        }} else {{
            chatContainer.style.display = 'none';
            button.innerHTML = '💬';
        }}
    }};
    
    widget.appendChild(chatContainer);
    widget.appendChild(button);
    document.body.appendChild(widget);
}})();
</script>'''

    return {
        "bot_id": bot_id,
        "iframe": iframe_code,
        "script": script_code,
        "instructions": "Copy and paste this code into your website's HTML"
    }


@router.get("/chat/{bot_id}", response_class=HTMLResponse)
async def chat_widget(bot_id: str):
    """Serve the chat widget iframe"""
    return FileResponse("app/templates/widget/chatbot.html")


@router.get("/widget.js")
async def get_widget_script():
    """Serve the widget JavaScript file"""
    return FileResponse("app/templates/widget/widget.js", media_type="application/javascript")
