<script setup>
import { ref, onMounted } from "vue";

const API_BASE = "http://127.0.0.1:8000";

// ---- Search ----
const query = ref("");
const results = ref([]);
const hasSearched = ref(false);
const searchError = ref("");

async function search() {
  searchError.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/search?query=${encodeURIComponent(query.value)}`);
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();
    results.value = data.results;
  } catch (err) {
    searchError.value = "Could not reach the server. Is the backend running?";
    results.value = [];
  } finally {
    hasSearched.value = true;
  }
}

// ---- Users (for the booking picker) ----
const users = ref([]);
const selectedUserId = ref("");

async function loadUsers() {
  const res = await fetch(`${API_BASE}/api/users`);
  const data = await res.json();
  users.value = data.users;
  if (users.value.length && !selectedUserId.value) {
    selectedUserId.value = users.value[0].user_id;
  }
}

// ---- Bookings / history ----
const bookings = ref([]);
const bookingError = ref("");
const bookingMessage = ref("");

async function loadBookings() {
  const res = await fetch(`${API_BASE}/api/bookings`);
  const data = await res.json();
  bookings.value = data.bookings;
}

async function bookTrip(tripId) {
  bookingError.value = "";
  bookingMessage.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/bookings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: selectedUserId.value, trip_id: tripId }),
    });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();
    bookingMessage.value = `Booked! New booking: ${data.booking_id}`;
    await loadBookings();
  } catch (err) {
    bookingError.value = "Could not create the booking.";
  }
}

async function cancelBooking(bookingId) {
  bookingError.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/bookings/${bookingId}/cancel`, { method: "PATCH" });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    await loadBookings();
  } catch (err) {
    bookingError.value = "Could not cancel the booking.";
  }
}

async function deleteBooking(bookingId) {
  bookingError.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/bookings/${bookingId}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    await loadBookings();
  } catch (err) {
    bookingError.value = "Could not delete the booking.";
  }
}

onMounted(() => {
  loadUsers();
  loadBookings();
});
</script>

<template>
  <main>
    <h1>Expedia Lite</h1>

    <section>
      <h2>Search</h2>
      <div class="search-bar">
        <input
          v-model="query"
          type="text"
          placeholder="Search hotel name or city..."
          @keyup.enter="search"
        />
        <button @click="search">Search</button>
      </div>

      <div class="user-picker">
        Booking as:
        <select v-model="selectedUserId">
          <option v-for="u in users" :key="u.user_id" :value="u.user_id">
            {{ u.display_name }}
          </option>
        </select>
      </div>

      <p v-if="searchError" class="error">{{ searchError }}</p>
      <p v-else-if="hasSearched && results.length === 0" class="no-results">
        No hotels matched "{{ query }}".
      </p>

      <table v-else-if="results.length" class="results">
        <thead>
          <tr>
            <th>Hotel</th>
            <th>City</th>
            <th>Trip</th>
            <th>Check-in</th>
            <th>Check-out</th>
            <th>Stay price</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="hotel in results" :key="hotel.hotel_id">
            <tr v-for="trip in hotel.trips" :key="trip.trip_id">
              <td>{{ hotel.hotel_name }}</td>
              <td>{{ hotel.city }}</td>
              <td>{{ trip.trip_name }}</td>
              <td>{{ trip.check_in }}</td>
              <td>{{ trip.check_out }}</td>
              <td>${{ trip.stay_price_usd }}</td>
              <td><button @click="bookTrip(trip.trip_id)">Book</button></td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>

    <section>
      <h2>Booking history</h2>
      <p v-if="bookingMessage" class="success">{{ bookingMessage }}</p>
      <p v-if="bookingError" class="error">{{ bookingError }}</p>

      <table v-if="bookings.length" class="results">
        <thead>
          <tr>
            <th>Booking</th>
            <th>Traveler</th>
            <th>Hotel</th>
            <th>Trip</th>
            <th>Dates</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.booking_id">
            <td>{{ b.booking_id }}</td>
            <td>{{ b.user_name }}</td>
            <td>{{ b.hotel_name }} ({{ b.city }})</td>
            <td>{{ b.trip_name }}</td>
            <td>{{ b.check_in }} → {{ b.check_out }}</td>
            <td>{{ b.status }}</td>
            <td class="actions">
              <button v-if="b.status !== 'cancelled'" @click="cancelBooking(b.booking_id)">
                Cancel
              </button>
              <button @click="deleteBooking(b.booking_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else>No bookings yet.</p>
    </section>
  </main>
</template>

<style scoped>
main {
  max-width: 1000px;
  margin: 2rem auto;
  font-family: system-ui, sans-serif;
}
section {
  margin-bottom: 2.5rem;
}
.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.search-bar input {
  flex: 1;
  padding: 0.5rem;
  font-size: 1rem;
}
.search-bar button,
.actions button {
  padding: 0.5rem 1rem;
  font-size: 0.95rem;
  cursor: pointer;
}
.user-picker {
  margin-bottom: 1rem;
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
.actions {
  display: flex;
  gap: 0.5rem;
}
.no-results {
  color: #555;
}
.error {
  color: #b00020;
}
.success {
  color: #1a7f37;
}
</style>