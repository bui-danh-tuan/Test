import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Box, Paper, TextField, Button, Typography, CircularProgress } from "@mui/material";

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMessage = { sender: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setQuestion("");

    try {
      const response = await axios.post("http://127.0.0.1:5000/chatbot", { question });
      const botMessage = { sender: "bot", text: response.data.answer };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error fetching response:", error);
      const errorMessage = { sender: "bot", text: "Lỗi kết nối đến server!" };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        width: "100vw",
        backgroundColor: "#121212",
        color: "white",
      }}
    >
      <Typography variant="h4" sx={{ mb: 2, fontWeight: "bold" }}>
        Chatbot UET
      </Typography>

      <Paper
        sx={{
          flex: 1,
          width: "80vw",
          maxWidth: "800px",
          overflowY: "auto",
          p: 2,
          backgroundColor: "#1e1e1e",
          borderRadius: 2,
        }}
        elevation={3}
      >
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              display: "flex",
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
              my: 1,
            }}
          >
            <Paper
              sx={{
                p: 2,
                maxWidth: "75%",
                borderRadius: 2,
                backgroundColor: msg.sender === "user" ? "#2196f3" : "#333",
                color: msg.sender === "user" ? "white" : "#ddd",
              }}
              elevation={2}
            >
              {msg.text}
            </Paper>
          </Box>
        ))}
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={chatEndRef}></div>
      </Paper>

      <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", width: "80vw", maxWidth: "800px", mt: 2 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Nhập câu hỏi..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          sx={{
            backgroundColor: "#1e1e1e",
            borderRadius: 1,
            input: { color: "white" },
            fieldset: { borderColor: "#555" },
            "&:hover fieldset": { borderColor: "#888" },
          }}
        />
        <Button
          type="submit"
          variant="contained"
          sx={{ ml: 2, bgcolor: "#1976d2", "&:hover": { bgcolor: "#1565c0" } }}
        >
          Gửi
        </Button>
      </Box>
    </Box>
  );
}

export default Chatbot;
