<script setup>
import { ref } from "vue";

const API_BASE = "http://127.0.0.1:8000";

const query = ref("");
const results = ref([]);
const hasSearched = ref(false);
const errorMessage = ref("");

async function search() {
  errorMessage.value = "";
  try {
    const res = await fetch(
      `${API_BASE}/api/search?query=${encodeURIComponent(query.value)}`
    );
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();
    results.value = data.results;
  } catch (err) {
    errorMessage.value = "Could not reach the server. Is the backend running?";
    results.value = [];
  } finally {
    hasSearched.value = true;
  }
}
</script>

<template>
  <main>
    <h1>Expedia Lite</h1>

    <div class="search-bar">
      <input
        v-model="query"
        type="text"
        placeholder="Search hotel name or city..."
        @keyup.enter="search"
      />
      <button @click="search">Search</button>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <p v-else-if="hasSearched && results.length === 0" class="no-results">
      No hotels matched "{{ query }}".
    </p>

    <table v-else-if="results.length" class="results">
      <thead>
        <tr>
          <th>Hotel</th>
          <th>City</th>
          <th>State</th>
          <th>Trip</th>
          <th>Check-in</th>
          <th>Check-out</th>
          <th>Nights</th>
          <th>Nightly rate</th>
          <th>Stay price</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="hotel in results" :key="hotel.hotel_id">
          <tr v-for="trip in hotel.trips" :key="trip.trip_id">
            <td>{{ hotel.hotel_name }}</td>
            <td>{{ hotel.city }}</td>
            <td>{{ hotel.state }}</td>
            <td>{{ trip.trip_name }}</td>
            <td>{{ trip.check_in }}</td>
            <td>{{ trip.check_out }}</td>
            <td>{{ trip.nights }}</td>
            <td>${{ hotel.nightly_rate_usd }}</td>
            <td>${{ trip.stay_price_usd }}</td>
          </tr>
        </template>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
main {
  max-width: 900px;
  margin: 2rem auto;
  font-family: system-ui, sans-serif;
}
.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.search-bar input {
  flex: 1;
  padding: 0.5rem;
  font-size: 1rem;
}
.search-bar button {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
}
table.results {
  width: 100%;
  border-collapse: collapse;
}
table.results th,
table.results td {
  border: 1px solid #ccc;
  padding: 0.5rem;
  text-align: left;
}
.no-results {
  color: #555;
}
.error {
  color: #b00020;
}
</style>
