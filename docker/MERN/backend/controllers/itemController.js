const Item = require("../models/itemModel"); // Import the Mongoose model

// Get all items
async function getItems(req, res) {
    try {
        const items = await Item.find(); // Use Mongoose's find method to get all items
        res.json(items);
    } catch (error) {
        res.status(500).json({ message: "Error fetching items", error });
    }
}

// Add a new item
async function addItem(req, res) {
    try {
        const newItem = new Item(req.body); // Create a new item using the Mongoose model
        const result = await newItem.save(); // Save the item to the database
        res.status(201).json({ insertedId: result._id });
    } catch (error) {
        res.status(400).json({ message: "Error adding item", error });
    }
}

// Update an item
async function updateItem(req, res) {
    const { id } = req.params;
    try {
        const updatedItem = await Item.findByIdAndUpdate(
            id,
            req.body,
            { new: true } // Return the updated document
        );
        if (!updatedItem) {
            return res.status(404).json({ message: "Item not found" });
        }
        res.json(updatedItem);
    } catch (error) {
        res.status(400).json({ message: "Error updating item", error });
    }
}

// Delete an item
async function deleteItem(req, res) {
    const { id } = req.params;
    try {
        const deletedItem = await Item.findByIdAndDelete(id);
        if (!deletedItem) {
            return res.status(404).json({ message: "Item not found" });
        }
        res.json({ message: "Item deleted", deletedItem });
    } catch (error) {
        res.status(400).json({ message: "Error deleting item", error });
    }
}

module.exports = { getItems, addItem, updateItem, deleteItem };
