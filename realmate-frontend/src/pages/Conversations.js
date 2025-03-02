import { useEffect, useState } from "react";
import { getConversations, getConversationById, sendMessage } from "../api"; // Criamos a função sendMessage
import "bootstrap/dist/css/bootstrap.min.css";
import { v4 as uuidv4 } from "uuid"; // Para gerar IDs únicos

export default function Conversations() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messageInput, setMessageInput] = useState(""); // Estado do input de mensagem
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
    if (!selectedConversation || !messageInput.trim()) return;

    const newMessage = {
      type: "NEW_MESSAGE",
      data: {
        id: uuidv4(), // Gerando um ID único
        conversation_id: selectedConversation.id,
        direction: "SENT",
        content: messageInput,
      },
      timestamp: new Date().toISOString(),
    };

    try {
      await sendMessage(newMessage); // Envia a mensagem para a API

      // Atualiza o estado local para exibir a nova mensagem na tela
      setSelectedConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, newMessage.data],
      }));

      setMessageInput(""); // Limpa o campo de input
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
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

          {/* Exibição de status da conversa */}
          {selectedConversation && selectedConversation.status === "CLOSED" ? (
            <p className="text-center fw-bold text-danger p-3">
              🚫 Mensagem fechada. Sem permissão para enviar ou receber mensagens.
            </p>
          ) : (
            selectedConversation && (
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
            )
          )}
        </div>
      </div>
    </div>
  );
}
