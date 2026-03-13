const Ajv = require("ajv");
const ajv = new Ajv();

const schema = {
  type: "object",
  properties: {
    filters: {
      type: "array",
      items: {
        type: "object",
        properties: {
          field: { type: "string" },
          operator: { type: "string" },
          value: {}
        },
        required: ["field", "operator", "value"]
      }
    },
    sector: { type: ["string", "null"] },
    sort: {
      type: ["object", "null"],
      properties: {
        field: { type: "string" },
        direction: { type: "string" }
      }
    },
    limit: { type: ["number", "null"] }
  },
  required: ["filters"]
};

const validate = ajv.compile(schema);

module.exports = validate;