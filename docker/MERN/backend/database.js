const { MongoClient } = require("mongodb");
require("dotenv").config();

const client = new MongoClient(process.env.MONGO_URI);

async function connectDB() {
    try {
        await client.connect();
        console.log("Connected to MongoDB");
        return client.db("YourDatabaseName").collection("items");
    } catch (error) {
        console.error("MongoDB connection error:", error);
    }
}

module.exports = connectDB;