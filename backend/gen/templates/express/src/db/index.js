// Picks the adapter for the database this project was generated for (see src/schema.js).
module.exports = require(require('../schema').db === 'mongodb' ? './mongo' : './sql');
