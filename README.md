# EchoMail 📬🔊

**EchoMail** is a multi-agent email assistant that classifies and summarizes incoming emails, and can even place a voice call to alert you of urgent messages. Built during the **Tenstorrent Multi-Agent Hackathon** using **Koyeb's cloud infrastructure** and powered by **Tenstorrent AI hardware**, EchoMail showcases the potential of agentic workflows and real-time AI integration.

## 🏆 Hackathon Highlights
- **Event**: Tenstorrent Multi-Agent Hackathon
- **Location**: San Francisco, CA
- **Result**: 🥇 First Place Winners

---

## 🚀 Features

- 🔐 **Gmail Authentication**: Securely connects to your Gmail inbox.
- 📥 **Email Processing**: Fetches and filters relevant incoming emails.
- 🧠 **Classification & Summarization**: Uses LLMs in an agentic flow to understand and summarize emails.
- 📞 **Urgent Alert System**: Integrates **Eleven Labs** to make AI voice calls for urgent emails.
- ⚡ **MCP Server**: Custom-built agent orchestration server for managing the agent flow.
- 💬 **Prompt Engineering**: Optimized prompts for agent coordination and decision-making.

## 🧠 Architecture Overview

Gmail API ➜ Email Fetcher ➜ Agentic Flow (LLMs) ➜ Email Classifier & Summarizer ➜
Urgent? ➜ Voice Call via Eleven Labs
⬇
Summarized Output

Agents communicate via a centralized **Multi-Agent Control Plane (MCP)** server, enabling collaboration between various AI models and external services.

## 🛠️ Tech Stack

- **Tenstorrent** — Hardware acceleration for AI workflows
- **Koyeb** — Scalable deployment infrastructure
- **Python** — Core application logic
- **FastAPI** — API server
- **Gmail API** — Email data source
- **Eleven Labs** — AI-generated voice alerts
- **LangChain / OpenAI APIs** — LLM orchestration

---

## 👨‍💻 Team EchoMail

- **Ben** – Gmail integration, authentication, and team coordination
- **Ramsha** – Email fetching and data handling
- **Som** – Multi-Agent Control Plane (MCP) development
- **Rishi** – Voice call integration using Eleven Labs
- **Aniruddha** – Prompt engineering and agentic flow design

---

## 📦 How to Run

1. **Clone the repo**
   git clone https://github.com/your-repo/echomail.git
   cd echomail

2. **Install dependencies**

   pip install -r requirements.txt

3. **Set up environment variables**

   * GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, ELEVEN_LABS_API_KEY, OPENAI_API_KEY, etc.

4. **Run the server**

   uvicorn main:app --reload

---

## 📄 License

This project is released under the [MIT License](https://www.mit.edu/~amini/LICENSE.md).

---

## 💬 Feedback & Contributions

We welcome feedback and collaboration! Reach out via [LinkedIn](https://www.linkedin.com/in/ben-katzir-332b54266/) or open an issue or PR.

---

Made with 🤖 and ☕ by Team EchoMail at the Tenstorrent Multi-Agent Hackathon.
