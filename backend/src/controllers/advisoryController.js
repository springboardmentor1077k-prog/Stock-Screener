const { generateStockAdvisory } = require("../services/advisoryService");

const getStockAdvisory = async (req, res) => {
  try {
    const { symbol } = req.params;

    const advisory = await generateStockAdvisory(symbol.toUpperCase());

    res.status(200).json({
      success: true,
      data: advisory
    });

  } catch (error) {
    res.status(400).json({
      success: false,
      message: error.message
    });
  }
};

module.exports = { getStockAdvisory };