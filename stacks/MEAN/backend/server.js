const express = require("express");
const cors = require("cors");
const itemRoutes = require("./routes/items");
const { DB_Connect } = require('./database');

const app = express();
const corsOptions = {
  origin: "*", // Allow all origins (for testing)
  methods: "GET,HEAD,PUT,PATCH,POST,DELETE",
  allowedHeaders: "Content-Type,Authorization",
};

app.use(cors(corsOptions));
app.use(express.json());

DB_Connect()
  .then(() => console.log("MongoDB Connected"))
  .catch((err) => console.error("MongoDB Connection Error:", err));

app.use("/api/items", itemRoutes);

app.use("/", (req, res) => {
  res.json({ message: "Hello world" });
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send({ message: err.message });
});

app.use((req, res) => {
    res.status(404).send({ message: "Route not found" });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
