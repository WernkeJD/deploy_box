const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const itemRoutes = require("./routes/items");
const mongoose = require('mongoose');

dotenv.config();

mongoose.connect(process.env.MONGO_URI )
    .then(() => console.log('Connected to MongoDB'))
    .catch((err) => console.error('Error connecting to MongoDB:', err));

const app = express();
app.use(express.json());
app.use(cors());

app.use("/", (req, res) => {
  res.json({ message: "Hello world" });
});

app.use("/api/items", itemRoutes);

app.use((req, res) => {
    res.status(404).send({ message: "Route not found" });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
