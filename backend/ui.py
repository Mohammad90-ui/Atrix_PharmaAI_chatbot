"""
Clinical Trial Query Chatbot - Modern Minimalistic UI
Professional, clean, and visually stunning interface.
"""
import gradio as gr
import requests
import uuid

# API Configuration
API_URL = "http://localhost:8001"
session_id = str(uuid.uuid4())


def chat_interface(user_message, history):
    """Handle chat interaction with beautiful formatting."""
    global session_id
    
    if not user_message.strip():
        return history, ""
    
    history.append([user_message, None])
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"session_id": session_id, "user_message": user_message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            assistant_msg = data["assistant_message"]
            source = data["source_citation"]
            
            # Format with elegant source badge
            if source and source != "none":
                formatted = f"{assistant_msg}\n\n<div style='margin-top: 12px; padding: 8px 12px; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 8px; display: inline-block;'><span style='color: white; font-size: 0.85em; font-weight: 500;'>📚 {source}</span></div>"
            else:
                formatted = assistant_msg
                
            history[-1][1] = formatted
        else:
            history[-1][1] = "⚠️ Unable to get response from server."
    
    except requests.exceptions.ConnectionError:
        history[-1][1] = "⚠️ Backend server not reachable. Please ensure it's running."
    except Exception as e:
        history[-1][1] = f"⚠️ Error: {str(e)}"
    
    return history, ""


def reset_conversation():
    """Reset chat session."""
    global session_id
    old_session_id = session_id
    session_id = str(uuid.uuid4())
    
    try:
        requests.post(f"{API_URL}/reset_session?session_id={old_session_id}")
    except:
        pass
    
    return []


def get_metrics():
    """Fetch and display metrics with beautiful formatting."""
    try:
        response = requests.get(f"{API_URL}/metrics")
        if response.status_code == 200:
            m = response.json()
            
            # Beautiful metric cards
            html = f"""
            <div style='background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);'>
                <div style='margin-bottom: 20px;'>
                    <div style='font-size: 2em; font-weight: 700; color: #6366f1; margin-bottom: 4px;'>{m['total_turns']}</div>
                    <div style='font-size: 0.9em; color: #64748b; font-weight: 500;'>Total Queries</div>
                </div>
                
                <div style='border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 16px;'>
                    <div style='font-weight: 600; color: #334155; margin-bottom: 12px; font-size: 0.95em;'>Source Distribution</div>
                    <div style='display: flex; flex-direction: column; gap: 8px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='color: #64748b; font-size: 0.9em;'>📊 Excel</span>
                            <span style='font-weight: 600; color: #6366f1;'>{m['source_usage']['excel_only']}</span>
                        </div>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='color: #64748b; font-size: 0.9em;'>📄 Doc</span>
                            <span style='font-weight: 600; color: #8b5cf6;'>{m['source_usage']['doc_only']}</span>
                        </div>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='color: #64748b; font-size: 0.9em;'>🔗 Both</span>
                            <span style='font-weight: 600; color: #10b981;'>{m['source_usage']['both']}</span>
                        </div>
                    </div>
                </div>
                
                <div style='border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 16px;'>
                    <div style='display: flex; flex-direction: column; gap: 8px;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span style='color: #64748b; font-size: 0.85em;'>❓ Clarifications</span>
                            <span style='font-weight: 600; color: #334155; font-size: 0.9em;'>{m['clarifications_asked']}</span>
                        </div>
                        <div style='display: flex; justify-content: space-between;'>
                            <span style='color: #64748b; font-size: 0.85em;'>🚫 Safety Blocks</span>
                            <span style='font-weight: 600; color: #334155; font-size: 0.9em;'>{m['safety_refusals']}</span>
                        </div>
                        <div style='display: flex; justify-content: space-between;'>
                            <span style='color: #64748b; font-size: 0.85em;'>❔ Unknown</span>
                            <span style='font-weight: 600; color: #334155; font-size: 0.9em;'>{m['unknown_responses']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """
            return html
        else:
            return "<div style='color: #ef4444; font-weight: 500;'>⚠️ Unable to fetch metrics</div>"
    except:
        return "<div style='color: #f59e0b; font-weight: 500;'>⚠️ Server not reachable</div>"


# Modern minimalistic CSS
modern_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

/* Header Styling */
.header-container {
    text-align: center;
    padding: 40px 20px 30px;
    background: white;
    border-radius: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    margin-bottom: 32px;
}

.main-title {
    font-size: 2.5em;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
    letter-spacing: -0.02em;
}

.subtitle {
    font-size: 1.05em;
    color: #64748b;
    font-weight: 500;
    margin-bottom: 20px;
}

.description {
    color: #475569;
    font-size: 0.95em;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
}

/* Chat Container */
#chatbot {
    border-radius: 20px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08) !important;
    border: none !important;
    background: white !important;
}

.message-wrap {
    padding: 16px !important;
}

.user.message {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 12px 16px !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
}

.bot.message {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 12px 16px !important;
    color: #1e293b !important;
}

/* Input Styling */
.input-container {
    background: white;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    margin-top: 16px;
}

textarea {
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    font-size: 0.95em !important;
    transition: all 0.3s ease !important;
}

textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    outline: none !important;
}

/* Buttons */
button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: none !important;
    font-size: 0.9em !important;
}

.primary {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
}

.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
}

.secondary {
    background: white !important;
    color: #6366f1 !important;
    border: 2px solid #e2e8f0 !important;
}

.secondary:hover {
    background: #f8fafc !important;
    border-color: #6366f1 !important;
}

/* Example Cards */
.examples {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    margin-top: 20px;
}

.example-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #475569;
    font-size: 0.9em;
}

.example-item:hover {
    background: #f1f5f9;
    border-color: #6366f1;
    transform: translateX(4px);
}

/* Sidebar */
.sidebar-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}

.sidebar-title {
    font-size: 1.1em;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 16px;
}

/* Metrics */
#metrics-display {
    min-height: 200px;
}

/* Feature Tags */
.feature-tag {
    display: inline-block;
    padding: 6px 12px;
    background: #f1f5f9;
    border-radius: 8px;
    color: #475569;
    font-size: 0.85em;
    font-weight: 500;
    margin: 4px;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.markdown {
    animation: fadeIn 0.4s ease;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
"""

# Build Interface
with gr.Blocks() as demo:
    # Header
    with gr.Row():
        with gr.Column():
            gr.HTML("""
                <div class='header-container'>
                    <div class='main-title'>🏥 Clinical Trial Intelligence</div>
                    <div class='subtitle'>AI-Powered Pharma Query Assistant</div>
                    <div class='description'>
                        Ask questions about drug dosing, adverse events, severity, outcomes, and label cautions. 
                        All answers are grounded in clinical trial data with full source citations.
                    </div>
                </div>
            """)
    
    # Main Content
    with gr.Row():
        # Chat Section
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(
                height=550,
                show_label=False,
                elem_id="chatbot",
                avatar_images=(
                    "https://api.dicebear.com/7.x/initials/svg?seed=U&backgroundColor=6366f1",
                    "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=AI&backgroundColor=8b5cf6"
                )
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="💬 Ask about drugs, dosing, adverse events, or label cautions...",
                    show_label=False,
                    scale=5,
                    container=False,
                    lines=1
                )
                submit = gr.Button("Send", scale=1, variant="primary")
            
            with gr.Row():
                clear = gr.Button("🔄 New Chat", size="sm", variant="secondary")
                
            with gr.Accordion("💡 Example Questions", open=False):
                gr.Examples(
                    examples=[
                        "What's the recommended dose for Metformin?",
                        "What AEs are reported for Pembrolizumab in melanoma?",
                        "Any cautions in the NSCLC label for Nivolumab?",
                        "How severe are Imatinib's hematological AEs?",
                        "What are the adverse events for Nivolumab?"
                    ],
                    inputs=msg,
                    label=None
                )
        
        # Sidebar
        with gr.Column(scale=3):
            with gr.Group():
                gr.Markdown("### 📊 Live Analytics")
                metrics = gr.HTML("<div style='color: #64748b; text-align: center; padding: 40px 20px;'>Click refresh to load</div>")
                refresh = gr.Button("🔄 Refresh", size="sm", variant="primary")
            
            with gr.Group():
                gr.Markdown("### ✨ Features")
                gr.HTML("""
                    <div style='display: flex; flex-wrap: wrap; gap: 8px;'>
                        <span class='feature-tag'>✅ Grounded</span>
                        <span class='feature-tag'>📚 Citations</span>
                        <span class='feature-tag'>🧠 Context-Aware</span>
                        <span class='feature-tag'>🛡️ Safe</span>
                        <span class='feature-tag'>⚡ Fast</span>
                    </div>
                """)
            
            with gr.Group():
                gr.Markdown("### 📖 Sources")
                gr.Markdown("""
                    <div style='font-size: 0.9em; color: #475569; line-height: 1.6;'>
                    <strong style='color: #6366f1;'>📊 Excel</strong><br/>
                    Structured data: dosing, AEs, severity<br/><br/>
                    <strong style='color: #8b5cf6;'>📄 Doc</strong><br/>
                    Label cautions, guidance notes
                    </div>
                """)
    
    # Event Handlers
    msg.submit(chat_interface, [msg, chatbot], [chatbot, msg])
    submit.click(chat_interface, [msg, chatbot], [chatbot, msg])
    clear.click(reset_conversation, None, chatbot)
    refresh.click(get_metrics, None, metrics)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        css=modern_css
    )
