const { EventEmitter } = require('events');
module.exports = new EventEmitter(); // 'change' -> { entity, op }
