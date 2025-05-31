import { useState, useRef, useEffect } from "react";
import axios from "axios";
import IconButton from '@mui/material/IconButton';
import SendIcon from '@mui/icons-material/Send';

import {
  Box,
  Paper,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";

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
      const response = await axios.post("http://127.0.0.1:5000/chatbot", {
        question,
      });

      const botMessage = {
        sender: "bot",
        text: response.data.answer,
        expected_answer: response.data.expected_answer,
        relevant_id: response.data.relevant_id,
        top_k_ids: response.data.top_k_ids,
        point: response.data.point,
        context: response.data.context,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error fetching response:", error);
      const errorMessage = {
        sender: "bot",
        text: "Lỗi kết nối đến server!",
      };
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
        height: "100vh",
        width: "100vw",
        backgroundColor: "#1e1e1e",
        color: "white",
      }}
    >
      <Typography
        variant="h5"
        sx={{ textAlign: "center", fontWeight: "bold", mb: 2 }}
      >
        Chatbot UET
      </Typography>

      <Paper
        sx={{
          flex: 1,
          width: "100%",
          maxWidth: "800px",
          margin: "0 auto",
          p: 2,
          backgroundColor: "#2a2a2a",
          borderRadius: 2,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          scrollbarWidth: "thin",
        }}
        elevation={3}
      >
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
              my: 1,
            }}
          >
            <Paper
              sx={{
                px: 2,
                py: 1,
                maxWidth: "75%",
                borderRadius: 10,
                backgroundColor: msg.sender === "user" ? "#424242" : "#333333",
                color: "#fff",
                whiteSpace: "pre-wrap",
                wordWrap: "break-word",
                boxShadow: "none",
              }}
              elevation={1}
            >
              {msg.text}
            </Paper>

            {/* Nếu là phản hồi từ bot, hiển thị từng phần theo thứ tự */}
            {msg.sender === "bot" && (
              <Box
                sx={{
                  maxWidth: "75%",
                  mt: 1,
                  fontSize: "0.9rem",
                  color: "#ccc",
                }}
              >
                {msg.expected_answer && (
                  <>
                    <Typography sx={{ fontWeight: "bold" }}>
                      ✅ Câu trả lời kỳ vọng:
                    </Typography>
                    <Typography sx={{ mb: 1, whiteSpace: "pre-wrap" }}>
                      {msg.expected_answer}
                    </Typography>
                  </>
                )}

                {msg.relevant_id && (
                  <Typography sx={{ mb: 1 }}>
                    🔗 ID đoạn văn đúng: <strong>{msg.relevant_id}</strong>
                  </Typography>
                )}

                {msg.top_k_ids && (
                  <Typography sx={{ mb: 1 }}>
                    🔍 Top {msg.top_k_ids.length} đoạn được truy hồi:{" "}
                    <strong>{msg.top_k_ids.join(", ")}</strong>
                  </Typography>
                )}

                {msg.point && (
                  <Typography sx={{ mb: 1 }}>
                    📊 Thang điểm đánh giá:{" "}
                    <strong>
                      {Object.entries(msg.point)
                        .map(([key, val]) => `${key}: ${val}`)
                        .join(" | ")}
                    </strong>
                  </Typography>
                )}

                {msg.context && (
                  <>
                    <Typography sx={{ fontWeight: "bold", mt: 2 }}>
                      📄 Ngữ cảnh sử dụng:
                    </Typography>
                    <Typography
                      sx={{
                        fontStyle: "italic",
                        color: "#aaa",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {msg.context}
                    </Typography>
                  </>
                )}
              </Box>
            )}

          </Box>
        ))}

        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
            <CircularProgress size={24} color="primary" />
          </Box>
        )}

        <div ref={chatEndRef}></div>
      </Paper>

      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          display: "flex",
          width: "100%",
          maxWidth: "800px",
          margin: "16px auto 0",
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Nhập câu hỏi của bạn..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          sx={{
            backgroundColor: "#2a2a2a",
            input: { color: "white" },
            borderRadius: 1,
          }}
        />
        <IconButton
          type="submit"
          sx={{
            ml: 1,
            color: "white",
            borderRadius: 1,
          }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}

export default Chatbot;
