import React, { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("Backend is not connected");
  const [items, setItems] = useState([]);

  useEffect(() => {
    axios
      .get("https://mern-backend-1038595011070.us-central1.run.app/api/items")
      .then((res) => {
        if (res.status === 200) {
          setMessage("Backend is connected");
          setItems(res.data);
          console.log(res.data);
        }
      })
      .catch((error) => console.error(error))
  }, []);

  return (
    <div>
      <h1>{message}</h1>
      <h2>Items</h2>
      <ul>
        {items.map((item) => (
          <li key={item._id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
