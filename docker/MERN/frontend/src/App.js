import React, { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("Waiting for response...");

  useEffect(() => {
    axios.get("http://localhost:5000/")
      .then((res) => setMessage(res.data))
      .catch((err) => console.log(err));
  }, []);

  return <h1>{message}</h1>;
}

export default App;
