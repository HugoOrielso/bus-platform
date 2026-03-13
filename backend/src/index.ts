import "dotenv/config";
import app from "./server";

const PORT = parseInt(process.env.PORT || "4000");

app.listen(PORT, "0.0.0.0", () => {
  console.log(`📍 API listening on port ${PORT}`);
});