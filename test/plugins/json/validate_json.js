const fs = require("fs");
const path = require("path");

const payloadPath = path.join(__dirname, "test_payload.json");

try {
  if (!fs.existsSync(payloadPath)) {
    throw new Error(`File not found ${payloadPath}`)
  }

  const rawData = fs.readFileSync(payloadPath, "utf8");

  const parsedData = JSON.parse(rawData)
  console.log("✅ JSON syntax is strictly compliant.");

  if (parsedData.username !== "oonamo") {
    throw new Error(`Expected username 'oonamo', got '${parsedData.username}'.`);
  }

  if (!Array.isArray(parsedData.posts) || parsedData.posts.length != 2) {
    throw new Error("Dynamic array 'posts' was not parsed correctly.");
  }

  if (parsedData.friends.includes("(null)")) {
    throw new Error("C Null pointer was leaked into json plugin.")
  }

  console.log("✅ Data ok.");
  process.exit(0);
} catch (error) {
  console.error("❌ JSON Validation Failed!");
  console.error(error.message);
  process.exit(1);
}
