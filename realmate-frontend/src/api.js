import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

export const getConversations = async () => {
  const response = await axios.get(`${API_BASE_URL}/conversations/`);
  return response.data;
};

export const getConversationById = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/conversations/${id}/`);
  return response.data;
};

export async function sendMessage(payload) {
  try {
    const response = await axios.post(`${API_BASE_URL}/webhook/`, payload, {
      headers: {
        "Content-Type": "application/json",
      },
    });

    return response.data; // Retorna a resposta da API
  } catch (error) {
    console.error("Erro na API:", error);
    throw error; // Lança o erro para ser tratado no componente
  }
}
