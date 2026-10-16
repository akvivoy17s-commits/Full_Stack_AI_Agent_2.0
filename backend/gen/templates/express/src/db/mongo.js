// MongoDB adapter (Mongoose). Same interface as sql.js. Schemas are built from src/schema.js.
const mongoose = require('mongoose');
const schema = require('../schema');
const cfg = require('../config');

const E = schema.entities;
const TYPES = { string: String, text: String, email: String, url: String, int: Number, float: Number, bool: Boolean, datetime: Date };
const entity = (n) => {
  if (!E[n]) throw new Error(`unknown entity ${n}`);
  return E[n];
};
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function model(e) {
  if (mongoose.models[e.name]) return mongoose.models[e.name];
  const def = {};
  for (const f of e.fields) {
    const d = f.type === 'ref' ? { type: mongoose.Schema.Types.ObjectId, ref: f.ref } : f.type === 'enum' ? { type: String, enum: f.values } : { type: TYPES[f.type] };
    if (f.required) d.required = true;
    if (f.unique) Object.assign(d, { unique: true, ...(f.required ? {} : { sparse: true }) });
    else if (f.index) d.index = true;
    def[f.name] = d;
  }
  return mongoose.model(e.name, new mongoose.Schema(def, { versionKey: false, collection: e.table }));
}

function fromDoc(e, d, raw) {
  if (!d) return null;
  const o = { id: String(d._id) };
  for (const f of e.fields) {
    if (!raw && e.sensitive.includes(f.name)) continue;
    let v = d[f.name];
    if (v === undefined) continue;
    if (v !== null) {
      if (f.type === 'ref') v = String(v);
      else if (f.type === 'datetime') v = new Date(v).toISOString();
    }
    o[f.name] = v;
  }
  return o;
}

const fix = (where) => Object.fromEntries(Object.entries(where).map(([k, v]) => [k === 'id' ? '_id' : k, v]));

async function connect() {
  await mongoose.connect(cfg.databaseUrl, { serverSelectionTimeoutMS: 5000 });
  const M = {};
  for (const e of Object.values(E)) {
    M[e.name] = model(e);
    await M[e.name].init(); // builds the unique and lookup indexes
  }
  const api = {
    kind: 'mongodb',
    parseId: (v) => (typeof v === 'string' && /^[a-f0-9]{24}$/i.test(v) ? v : null),
    clean: (name, r) => fromDoc(entity(name), { ...r, _id: r.id }, false),
    async get(name, id, opt = {}) {
      return api.parseId(String(id)) ? fromDoc(entity(name), await M[name].findById(id).lean(), opt.raw) : null;
    },
    async findOne(name, where, opt = {}) {
      return fromDoc(entity(name), await M[name].findOne(fix(where)).lean(), opt.raw);
    },
    async list(name, { where = {}, filters = {}, q, page = 1, limit = 20, sort = { field: 'id', dir: 'desc' } } = {}) {
      const e = entity(name);
      const filter = fix({ ...where, ...filters });
      if (q && e.searchable.length) filter.$or = e.searchable.map((f) => ({ [f]: { $regex: esc(q), $options: 'i' } }));
      const [total, rows] = await Promise.all([
        M[name].countDocuments(filter),
        M[name].find(filter).sort(sort.field === 'id' ? { _id: sort.dir === 'asc' ? 1 : -1 } : { [sort.field]: sort.dir === 'asc' ? 1 : -1, _id: -1 }).skip((page - 1) * limit).limit(limit).lean(),
      ]);
      return { rows: rows.map((r) => fromDoc(e, r)), total };
    },
    async create(name, data) {
      const doc = await M[name].create(data);
      return fromDoc(entity(name), doc.toObject());
    },
    async update(name, id, data) {
      return fromDoc(entity(name), await M[name].findByIdAndUpdate(id, { $set: data }, { new: true, runValidators: true, lean: true }));
    },
    async remove(name, id) {
      return (await M[name].findByIdAndDelete(id)) != null;
    },
    async removeWhere(name, where) {
      return (await M[name].deleteMany(fix(where))).deletedCount;
    },
    migrate: async () => {},
    ping: () => mongoose.connection.db.command({ ping: 1 }),
    close: () => mongoose.disconnect(),
  };
  return api;
}

module.exports = { connect };
