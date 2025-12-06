/* jshint esversion: 8 */

const express = require('express');
const mongoose = require('mongoose');
const fs = require('fs');
const cors = require('cors');
const app = express();
const port = 3030;

app.use(cors());
app.use(require('body-parser').urlencoded({ extended: false }));

const reviewsData = JSON.parse(fs.readFileSync('reviews.json', 'utf8'));
const dealershipsData = JSON.parse(fs.readFileSync('dealerships.json', 'utf8'));

mongoose.connect('mongodb://mongo_db:27017/', { dbName: 'dealershipsDB' });

const Reviews = require('./review');
const Dealerships = require('./dealership');

// Load seed data
(async () => {
    try {
        await Reviews.deleteMany({});
        await Reviews.insertMany(reviewsData.reviews);

        await Dealerships.deleteMany({});
        await Dealerships.insertMany(dealershipsData.dealerships);
    } catch (error) {
        console.error('Startup data load error:', error);
    }
})();

// Express route to home
app.get('/', async (req, res) => {
    res.send('Welcome to the Mongoose API');
});

// Express route to fetch all reviews
app.get('/fetchReviews', async (req, res) => {
    try {
        const documents = await Reviews.find();
        res.json(documents);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching documents' });
    }
});

// Express route to fetch reviews by a particular dealer
app.get('/fetchReviews/dealer/:id', async (req, res) => {
    try {
        const documents = await Reviews.find({ dealership: req.params.id });
        res.json(documents);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching documents' });
    }
});

// Express route to fetch all dealerships
app.get('/fetchDealers', async (req, res) => {
    try {
        const dealers = await Dealerships.find();
        res.json(dealers);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching dealerships' });
    }
});

// Express route to fetch Dealers by state (case-insensitive exact match)
app.get('/fetchDealers/:state', async (req, res) => {
    try {
        const state = req.params.state;
        const dealers = await Dealerships.find({
            state: { $regex: new RegExp(`^${state}$`, 'i') }
        });
        res.json(dealers);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching dealerships by state' });
    }
});

// Fetch a single dealership by numeric ID or Mongo ObjectId
app.get('/fetchDealer/:id', async (req, res) => {
    try {
        const idParam = req.params.id;
        const numericId = Number(idParam);
        let dealer = null;

        if (!Number.isNaN(numericId)) {
            dealer = await Dealerships.findOne({ id: numericId });
        }

        if (!dealer && mongoose.Types.ObjectId.isValid(idParam)) {
            dealer = await Dealerships.findById(idParam);
        }

        if (!dealer) {
            return res.status(404).json({ error: 'Dealership not found' });
        }

        res.json(dealer);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching dealership' });
    }
});

// Insert a new review
app.post('/insert_review', express.raw({ type: '*/*' }), async (req, res) => {
    let data = JSON.parse(req.body);

    const documents = await Reviews.find().sort({ id: -1 });
    let newId = documents[0].id + 1;

    const review = new Reviews({
        id: newId,
        name: data.name,
        dealership: data.dealership,
        review: data.review,
        purchase: data.purchase,
        purchase_date: data.purchase_date,
        car_make: data.car_make,
        car_model: data.car_model,
        car_year: data.car_year
    });

    try {
        const savedReview = await review.save();
        res.json(savedReview);
    } catch (error) {
        console.log(error);
        res.status(500).json({ error: 'Error inserting review' });
    }
});

// Start the Express server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
