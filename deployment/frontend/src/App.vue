<template>
  <v-app :theme="theme">
    <v-main v-if="!isAuthenticated">
      <v-container class="fill-height">
        <v-row justify="center" align="center">
          <v-col cols="12" sm="8" md="4">
            <v-card class="pa-4">
              <v-tabs v-model="authTab" align-tabs="center" color="primary">
                <v-tab value="login">Login</v-tab>
                <v-tab value="signup">Sign Up</v-tab>
              </v-tabs>
              <v-card-text>
                <v-form @submit.prevent="authTab === 'login' ? login() : signup()">
                  <v-text-field v-if="authTab === 'signup'" v-model="username" label="Username" prepend-icon="mdi-account"></v-text-field>
                  <v-text-field v-model="email" label="Email" prepend-icon="mdi-email"></v-text-field>
                  <v-text-field v-model="password" label="Password" type="password" prepend-icon="mdi-lock"></v-text-field>
                  <v-btn type="submit" color="primary" block class="mt-2">{{ authTab === 'login' ? 'Login' : 'Sign Up' }}</v-btn>
                </v-form>
                <v-alert v-if="authMessage" :type="authSuccess ? 'success' : 'error'" class="mt-2">{{ authMessage }}</v-alert>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <v-app-bar v-if="isAuthenticated" color="primary">
      <v-app-bar-title>ISMAP - Subdomain & Vulnerability Scanner</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="toggleTheme"><v-icon>{{ theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon></v-btn>
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props"><v-icon>mdi-account</v-icon></v-btn>
        </template>
        <v-list>
          <v-list-item><v-list-item-title>Logged in as: {{ username }}</v-list-item-title><v-list-item-subtitle v-if="isAdmin">Admin</v-list-item-subtitle></v-list-item>
          <v-list-item @click="logout"><v-list-item-title>Logout</v-list-item-title></v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-main v-if="isAuthenticated">
      <v-container>
        <v-expand-transition>
          <v-card v-if="isAdmin" class="mb-4" v-show="showAdmin">
            <v-card-title>Admin Dashboard - User Management</v-card-title>
            <v-card-text><v-data-table :headers="userHeaders" :items="users" :items-per-page="5"></v-data-table></v-card-text>
          </v-card>
        </v-expand-transition>

        <v-row>
          <v-col cols="12" md="6">
            <v-card>
              <v-card-title>Register Domain</v-card-title>
              <v-card-text>
                <v-text-field v-model="newDomain" label="Domain (e.g., example.com)" prepend-icon="mdi-web"></v-text-field>
                <v-select v-model="scanInterval" :items="[1, 6, 12, 24, 48]" label="Scan every (hours)" prepend-icon="mdi-clock"></v-select>
                <v-btn color="primary" @click="registerDomain" :loading="loading">Register</v-btn>
                <v-alert v-if="registerMessage" :type="registerSuccess ? 'success' : 'error'" class="mt-2">{{ registerMessage }}</v-alert>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card>
              <v-card-title>Configure Alerts</v-card-title>
              <v-card-text>
                <v-text-field v-model="alertConfig.slack_webhook" label="Slack Webhook URL" prepend-icon="mdi-slack"></v-text-field>
                <v-text-field v-model="alertConfig.telegram_bot_token" label="Telegram Bot Token" prepend-icon="mdi-telegram"></v-text-field>
                <v-text-field v-model="alertConfig.telegram_chat_id" label="Telegram Chat ID" prepend-icon="mdi-chat"></v-text-field>
                <v-btn color="primary" @click="configureAlerts" :loading="loading">Save Settings</v-btn>
                <v-alert v-if="alertMessage" :type="alertSuccess ? 'success' : 'error'" class="mt-2">{{ alertMessage }}</v-alert>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-row class="mt-4">
          <v-col cols="12">
            <v-card>
              <v-card-title><v-row><v-col>Discover Subdomains</v-col><v-col align="end"><v-btn color="success" @click="discoverAll" :loading="scanning">Start Scan</v-btn></v-col></v-row></v-card-title>
              <v-card-text>
                <v-text-field v-model="scanDomain" label="Enter domain to scan" prepend-icon="mdi-magnify"></v-text-field>
                <v-progress-linear v-if="scanning" indeterminate color="primary" class="mb-2"></v-progress-linear>
                <v-alert v-if="scanError" type="error" class="mb-2">{{ scanError }}</v-alert>
                <v-data-table v-if="results.length" :headers="resultHeaders" :items="results" class="mt-2">
                  <template v-slot:item.vulnerabilities="{ item }">
                    <v-chip v-for="vuln in item.vulnerabilities" :key="vuln" :color="vuln.severity === 'High' ? 'error' : 'warning'" size="small" class="mr-1">{{ vuln.name }}</v-chip>
                    <span v-if="!item.vulnerabilities || item.vulnerabilities.length === 0">None</span>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-row class="mt-4">
          <v-col cols="12" md="6">
            <v-card>
              <v-card-title>Scan History</v-card-title>
              <v-card-text>
                <v-text-field v-model="historyDomain" label="Enter domain" prepend-icon="mdi-history"></v-text-field>
                <v-btn color="info" @click="loadHistory" :loading="loadingHistory">Load History</v-btn>
                <v-alert v-if="historyError" type="error" class="mt-2">{{ historyError }}</v-alert>
                <v-timeline v-if="history.length" density="compact" class="mt-2">
                  <v-timeline-item v-for="h in history" :key="h.id" dot-color="success" size="small">
                    <strong>{{ h.timestamp }}</strong><br>
                    <span v-if="h.changes && h.changes.new">+{{ h.changes.new.length }} new</span>
                  </v-timeline-item>
                </v-timeline>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card>
              <v-card-title>Export Report</v-card-title>
              <v-card-text>
                <v-text-field v-model="exportDomain" label="Enter domain" prepend-icon="mdi-download"></v-text-field>
                <v-btn color="warning" @click="exportReport" :loading="exporting">Download</v-btn>
                <v-alert v-if="exportError" type="error" class="mt-2">{{ exportError }}</v-alert>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      theme: 'dark', isAuthenticated: false, authTab: 'login',
      username: '', email: '', password: '',
      authMessage: '', authSuccess: false, isAdmin: false,
      newDomain: '', scanInterval: 6,
      registerMessage: '', registerSuccess: false,
      alertConfig: { slack_webhook: '', telegram_bot_token: '', telegram_chat_id: '' },
      alertMessage: '', alertSuccess: false,
      loading: false, scanning: false, scanDomain: '', results: [], scanError: '',
      showAdmin: false, users: [], historyDomain: '', exportDomain: '', history: [], historyError: '', exportError: '',
      loadingHistory: false, exporting: false,
      userHeaders: [{title:'ID',key:'id'},{title:'Username',key:'username'},{title:'Email',key:'email'}],
      resultHeaders: [{title:'Subdomain',key:'subdomain'},{title:'IP',key:'ip'},{title:'Status',key:'status_code'},{title:'Vulnerabilities',key:'vulnerabilities'}]
    };
  },
  methods: {
    toggleTheme() { this.theme = this.theme === 'dark' ? 'light' : 'dark'; },
    async login() {
      try {
        const res = await axios.post('http://localhost:5000/api/login', {email: this.email, password: this.password});
        this.token = res.data.token; this.isAdmin = res.data.is_admin; this.username = res.data.username;
        this.isAuthenticated = true;
        localStorage.setItem('token', this.token);
        localStorage.setItem('isAdmin', this.isAdmin);
        localStorage.setItem('username', this.username);
      } catch(e) { this.authMessage = 'Invalid credentials'; this.authSuccess = false; }
    },
    async signup() {
      try {
        await axios.post('http://localhost:5000/api/register', {username: this.username, email: this.email, password: this.password});
        this.authMessage = 'Account created! Please login.'; this.authSuccess = true; this.authTab = 'login';
      } catch(e) { this.authMessage = 'Username or email exists'; this.authSuccess = false; }
    },
    logout() { this.isAuthenticated = false; this.isAdmin = false; localStorage.clear(); window.location.reload(); },
    async registerDomain() {
      this.loading = true;
      try {
        await axios.post('http://localhost:5000/register/' + this.newDomain);
        this.registerMessage = 'Domain registered!'; this.registerSuccess = true;
      } catch(e) { this.registerMessage = 'Error'; this.registerSuccess = false; }
      this.loading = false;
    },
    async configureAlerts() {
      this.loading = true;
      try {
        await axios.post('http://localhost:5000/configure_alerts', this.alertConfig);
        this.alertMessage = 'Saved!'; this.alertSuccess = true;
      } catch(e) { this.alertMessage = 'Error'; this.alertSuccess = false; }
      this.loading = false;
    },
    async discoverAll() {
      if (!this.scanDomain) return;
      this.scanning = true; this.scanError = ''; this.results = [];
      try {
        const response = await axios.get('http://localhost:5000/discover/' + this.scanDomain);
        this.results = response.data.subdomains.map(sub => ({...sub, vulnerabilities: sub.vulnerabilities || []}));
      } catch(e) { this.scanError = 'Error scanning'; }
      this.scanning = false;
    },
    async loadHistory() {
      if (!this.historyDomain) return;
      this.loadingHistory = true; this.historyError = ''; this.history = [];
      try {
        const response = await axios.get('http://localhost:5000/api/history/' + this.historyDomain);
        this.history = response.data || [];
      } catch(e) { this.historyError = 'Error loading'; }
      this.loadingHistory = false;
    },
    async exportReport() {
      if (!this.exportDomain) return;
      this.exporting = true; this.exportError = '';
      try {
        const response = await axios.get('http://localhost:5000/api/export/' + this.exportDomain);
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {type: 'application/json'});
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = this.exportDomain + '_report.json'; a.click();
      } catch(e) { this.exportError = 'Error exporting'; }
      this.exporting = false;
    },
    checkAuth() {
      const token = localStorage.getItem('token');
      if (token) { this.token = token; this.isAdmin = localStorage.getItem('isAdmin') === 'true'; this.username = localStorage.getItem('username'); this.isAuthenticated = true; }
    }
  },
  mounted() { this.checkAuth(); }
};
</script>

<style>html { overflow-y: auto; }</style>