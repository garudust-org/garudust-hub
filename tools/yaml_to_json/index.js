#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

const filePath = process.argv[2];

if (!filePath) {
  console.error("Error: file path required");
  process.exit(1);
}

let content;
try {
  content = fs.readFileSync(filePath, "utf8");
} catch (e) {
  console.error(`Error reading ${filePath}: ${e.message}`);
  process.exit(1);
}

let parsed;
try {
  parsed = yaml.load(content);
} catch (e) {
  console.error(`Error parsing YAML: ${e.message}`);
  process.exit(1);
}

console.log(JSON.stringify(parsed, null, 2));
