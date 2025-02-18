import React, { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("Backend is not connected");

  useEffect(() => {
    axios
      .get("http://localhost:5000/")
      .then((res) => {
        if (res.status === 200) {
          setMessage("Backend is connected");
        }
      })
      .catch((error) => console.error(error))
  }, []);

  return (
    <div>
      <h1>{message}</h1>
    </div>
  );
}

export default App;
