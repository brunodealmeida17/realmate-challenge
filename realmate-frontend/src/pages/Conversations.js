import { useEffect, useState } from "react";
import { getConversations, getConversationById, sendMessage } from "../api";
import "bootstrap/dist/css/bootstrap.min.css";
import { v4 as uuidv4 } from "uuid";
import axios from "axios";

export default function Conversations() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messageInput, setMessageInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getConversations().then(setConversations);
  }, []);

  const handleSelectConversation = async (conversationId) => {
    setLoading(true);
    try {
      const conversationData = await getConversationById(conversationId);
      setSelectedConversation(conversationData);
    } catch (error) {
      console.error("Erro ao carregar conversa:", error);
    }
    setLoading(false);
  };

  const handleSendMessage = async () => {
    if (!selectedConversation || !messageInput.trim() || selectedConversation.status === "CLOSED") return;

    const newMessage = {
      type: "NEW_MESSAGE",
      data: {
        id: uuidv4(),
        conversation_id: selectedConversation.id,
        direction: "SENT",
        content: messageInput,
      },
      timestamp: new Date().toISOString(),
    };

    try {
      await sendMessage(newMessage);

      setSelectedConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, newMessage.data],
      }));

      setMessageInput("");
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
    }
  };

  const handleCloseConversation = async () => {
    if (!selectedConversation) return;

    const payload = {
      type: "CLOSE_CONVERSATION",
      data: { id: selectedConversation.id },
    };

    try {
      await axios.post("http://127.0.0.1:8000/api/webhook/", payload, {
        headers: { "Content-Type": "application/json" },
      });

      setSelectedConversation((prev) => ({
        ...prev,
        status: "CLOSED",
      }));
    } catch (error) {
      console.error("Erro ao fechar conversa:", error);
    }
  };

  return (
    <div className="container mt-4">
      <h1 className="text-primary mb-4">Conversas</h1>
      <div className="row">
        {/* Lista de conversas */}
        <div className="col-md-4 border-end" style={{ height: "80vh", overflowY: "auto" }}>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className="card shadow-sm p-3 mb-3 text-center conversation-card"
              onClick={() => handleSelectConversation(conv.id)}
              style={{
                cursor: "pointer",
                background: selectedConversation?.id === conv.id ? "#e6f7ff" : "white",
              }}
            >
              <h5 className="card-title">{conv.id}</h5>
              <p className={`status ${conv.status.toLowerCase()}`} style={{ color: conv.status === "OPEN" ? "green" : "red" }}>
                {conv.status}
              </p>
            </div>
          ))}
        </div>

        {/* Mensagens da conversa */}
        <div className="col-md-8 d-flex flex-column" style={{ height: "80vh" }}>
          <div className="flex-grow-1 overflow-auto p-3">
            {loading ? (
              <p>Carregando mensagens...</p>
            ) : selectedConversation ? (
              <>
                <h4>Conversa: {selectedConversation.id}</h4>

                {/* Botão Fechar Conversa (aparece apenas se estiver aberta) */}
                {selectedConversation.status === "OPEN" && (
                  <button className="btn btn-danger mb-3" onClick={handleCloseConversation}>
                    Fechar Conversa
                  </button>
                )}

                <p className={selectedConversation.status === "CLOSED" ? "text-danger fw-bold" : ""}>
                  {selectedConversation.status === "CLOSED"
                    ? " 🚫 Mensagem fechada. Sem permissão para enviar ou receber mensagens."
                    : ""}
                </p>

                <div className="chat-box">
                  {selectedConversation.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`message ${msg.direction === "SENT" ? "sent" : "received"}`}
                    >
                      {msg.content}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p>Selecione uma conversa para visualizar as mensagens.</p>
            )}
          </div>

          {/* Campo de entrada de mensagem */}
          {selectedConversation && selectedConversation.status === "OPEN" && (
            <div className="p-3 border-top d-flex">
              <input
                type="text"
                className="form-control me-2"
                placeholder="Digite sua mensagem..."
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              />
              <button className="btn btn-primary" onClick={handleSendMessage}>
                Enviar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
