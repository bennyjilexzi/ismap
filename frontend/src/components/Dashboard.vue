<template>
  <div class="dashboard">
    <h1>ISMAP Dashboard</h1>
    
    <div class="section">
      <h2>Register Domain</h2>
      <input v-model="newDomain" placeholder="Enter domain (e.g., example.com)" />
      <button @click="registerDomain">Register</button>
      <p v-if="registerMessage">{{ registerMessage }}</p>
    </div>

    <div class="section">
      <h2>Discover Subdomains</h2>
      <input v-model="discoverDomain" placeholder="Enter domain" />
      <button @click="discoverSubdomains">Discover</button>
      <div v-if="discoveredSubs.length">
        <h3>Results:</h3>
        <ul>
          <li v-for="sub in discoveredSubs" :key="sub.subdomain">
            {{ sub.subdomain }} - {{ sub.ip }} - {{ sub.status_code }}
          </li>
        </ul>
      </div>
    </div>

    <div class="section">
      <h2>Configure Alerts</h2>
      <input v-model="alertConfig.slack_webhook" placeholder="Slack Webhook URL" /><br/>
      <input v-model="alertConfig.telegram_bot_token" placeholder="Telegram Bot Token" /><br/>
      <input v-model="alertConfig.telegram_chat_id" placeholder="Telegram Chat ID" /><br/>
      <button @click="configureAlerts">Save Alert Settings</button>
      <p v-if="alertMessage">{{ alertMessage }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Dashboard',
  data() {
    return {
      newDomain: '',
      discoverDomain: '',
      discoveredSubs: [],
      registerMessage: '',
      alertMessage: '',
      alertConfig: {
        slack_webhook: '',
        telegram_bot_token: '',
        telegram_chat_id: ''
      }
    };
  },
  methods: {
    async registerDomain() {
      try {
        const response = await axios.post(`http://localhost:5000/register/${this.newDomain}`);
        this.registerMessage = response.data.message;
      } catch (error) {
        this.registerMessage = 'Error: ' + error.message;
      }
    },
    async discoverSubdomains() {
      try {
        const response = await axios.get(`http://localhost:5000/discover/${this.discoverDomain}`);
        this.discoveredSubs = response.data.subdomains;
      } catch (error) {
        console.error('Error:', error);
      }
    },
    async configureAlerts() {
      try {
        const response = await axios.post('http://localhost:5000/configure_alerts', this.alertConfig);
        this.alertMessage = response.data.message;
      } catch (error) {
        this.alertMessage = 'Error: ' + error.message;
      }
    }
  }
};
</script>

<style scoped>
.dashboard { padding: 20px; font-family: Arial, sans-serif; }
.section { margin-bottom: 30px; border: 1px solid #ccc; padding: 15px; border-radius: 5px; }
input { padding: 8px; margin: 5px; width: 300px; }
button { padding: 8px 15px; background: #007bff; color: white; border: none; cursor: pointer; }
button:hover { background: #0056b3; }
ul { list-style: none; padding: 0; }
li { padding: 5px; border-bottom: 1px solid #eee; }
</style>
