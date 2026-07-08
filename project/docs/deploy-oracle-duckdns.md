# Deploy Nexus for free on Oracle Cloud + DuckDNS

**Cost: $0/month** — Oracle Always Free VM + free DuckDNS subdomain + automatic HTTPS.

---

## Overview

| Step | What you do | Time |
|------|-------------|------|
| 1 | Create Oracle Cloud account + VM | ~15 min |
| 2 | Open firewall ports 22, 80, 443 | ~5 min |
| 3 | Create DuckDNS subdomain | ~2 min |
| 4 | SSH in, install Docker, deploy | ~10 min |

Your site will be live at: `https://yournexus.duckdns.org`

---

## Step 1 — Create Oracle Cloud VM

### 1.1 Sign up

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and create a **Free Tier** account.
2. Verify email and add a payment method (Oracle requires it for free tier; you won't be charged if you stay within free limits).

### 1.2 Create the VM

1. Menu → **Compute** → **Instances** → **Create instance**
2. **Name:** `nexus`
3. **Image:** Ubuntu 22.04 (or 24.04)
4. **Shape:** Click **Change shape** → **Ampere** → **VM.Standard.A1.Flex**
   - OCPUs: **2** (or up to 4 — all free)
   - Memory: **12 GB** (or up to 24 GB — all free)
5. **Networking:** Use default VCN — ensure **Assign a public IPv4 address** is checked
6. **SSH keys:** Upload your public key, or let Oracle generate one and download the private key
7. Click **Create**

> **"Out of capacity"?** Try a different **Availability Domain** or region (e.g. Phoenix, Ashburn, Frankfurt).

### 1.3 Note your public IP

On the instance page, copy the **Public IP address** (e.g. `129.213.45.67`).

---

## Step 2 — Open firewall ports (critical)

Oracle blocks traffic by default. You must open ports **22**, **80**, and **443**.

### 2.1 Security List (VCN)

1. Instance page → click your **Subnet** link → click the **Security List**
2. **Add Ingress Rules** — add these three rules:

| Source CIDR | Protocol | Destination port |
|-------------|----------|------------------|
| `0.0.0.0/0` | TCP | 22 |
| `0.0.0.0/0` | TCP | 80 |
| `0.0.0.0/0` | TCP | 443 |

3. Save

### 2.2 Ubuntu firewall (on the VM, after SSH)

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

If `netfilter-persistent` is not installed:

```bash
sudo apt-get install -y iptables-persistent
# answer Yes to save current rules
```

---

## Step 3 — DuckDNS subdomain

1. Go to [duckdns.org](https://www.duckdns.org) and sign in (Google/GitHub/etc.)
2. Create a subdomain, e.g. `yournexus` → **`yournexus.duckdns.org`**
3. Set the **IP** to your Oracle VM **public IP** from Step 1.3
4. Click **update ip**

Verify (from your laptop):

```bash
ping yournexus.duckdns.org
# should show your Oracle VM IP
```

---

## Step 4 — SSH into the VM

```bash
# If you downloaded Oracle's private key:
chmod 600 ~/Downloads/ssh-key-*.key
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_PUBLIC_IP

# Or with your own key:
ssh ubuntu@YOUR_PUBLIC_IP
```

---

## Step 5 — Install Docker

On the VM:

```bash
curl -fsSL https://raw.githubusercontent.com/ShubhamRSY/voice-agents/main/scripts/install-docker.sh | bash
```

**Log out and SSH back in** so the `docker` group applies:

```bash
exit
ssh ubuntu@YOUR_PUBLIC_IP
docker compose version   # should print a version
```

---

## Step 6 — Deploy Nexus

```bash
git clone https://github.com/ShubhamRSY/voice-agents.git
cd voice-agents
DOMAIN=yournexus.duckdns.org bash scripts/deploy-public.sh
```

When prompted for DNS, confirm DuckDNS already points to this server (press Enter).

The script will:
- Generate JWT, database password, and encryption keys
- Write `config/environment/.env`
- Build and start Caddy + Postgres + Redis + Nexus
- Provision HTTPS via Let's Encrypt (1–2 minutes)

---

## Step 7 — Verify

Open in your browser:

- **Website:** `https://yournexus.duckdns.org`
- **Health:** `https://yournexus.duckdns.org/api/v1/health`

Register your first admin account:

```bash
curl -X POST https://yournexus.duckdns.org/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "YourSecurePass123!",
    "name": "Admin",
    "tenant_name": "My Company"
  }'
```

Then log in via the web UI or API:

```bash
curl -X POST https://yournexus.duckdns.org/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YourSecurePass123!"}'
```

---

## Optional — OpenAI API key

For real AI responses (not mock), add your key after deploy:

```bash
nano config/environment/.env
# Set: OPENAI_API_KEY=sk-your-key-here
docker compose -f deploy/docker/docker-compose.yml up -d
```

---

## Useful commands

```bash
cd ~/voice-agents

# View logs
docker compose -f deploy/docker/docker-compose.yml logs -f nexus

# Restart everything
docker compose -f deploy/docker/docker-compose.yml restart

# Stop
docker compose -f deploy/docker/docker-compose.yml down

# Update to latest code
git pull
docker compose -f deploy/docker/docker-compose.yml up -d --build
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **Can't SSH** | Check Security List has port 22 open; use `ubuntu` user |
| **Site won't load** | Check ports 80/443 in Security List + Ubuntu iptables |
| **HTTPS certificate error** | Wait 2 min; ensure DuckDNS IP matches VM IP |
| **"Out of capacity" on Oracle** | Try another Availability Domain or region |
| **DuckDNS IP changed** | Oracle free VMs keep IP until you stop/delete instance; update DuckDNS if IP changes |
| **Build fails (low memory)** | Use shape with at least 2 OCPU / 12 GB RAM |

### Check Caddy HTTPS logs

```bash
docker compose -f deploy/docker/docker-compose.yml logs caddy
```

### Check Nexus health inside container

```bash
docker compose -f deploy/docker/docker-compose.yml exec nexus \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').read())"
```

---

## Save your secrets

After deploy, back up these from `config/environment/.env`:

- `JWT_SECRET`
- `POSTGRES_PASSWORD`
- `INTEGRATIONS_ENCRYPTION_KEY`
- `SETTINGS_ADMIN_TOKEN`

If you lose them, existing sessions and encrypted credentials cannot be recovered.

---

## Cost reminder

| Resource | Cost |
|----------|------|
| Oracle Ampere A1 (within free limits) | **$0** |
| DuckDNS subdomain | **$0** |
| Let's Encrypt HTTPS | **$0** |

Stay within Oracle Always Free limits (1–4 OCPUs, up to 24 GB RAM on A1 flex).
