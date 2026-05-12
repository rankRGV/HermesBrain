# HermesBrain

Central repo for the RankRGV Hermes VPS setup.

This repo is meant to hold the parts that should survive across Hermes reinstalls:

- deterministic scripts
- client and workflow context
- provider setup templates
- operating notes for prospecting and SEO tasks

It should not store live secrets or a copied `~/.hermes` directory.

## Structure

```text
context/         Business context Hermes should read
docs/            Setup notes and integration docs
prompts/         Reusable prompt templates
scripts/         Deterministic automation and bootstrap scripts
.env.example     Template for server-side secrets
```

## VPS Setup

Clone onto the VPS:

```bash
cd /root
git clone https://github.com/rankRGV/HermesBrain.git
cd /root/HermesBrain
```

Create the runtime env file:

```bash
cp .env.example .env
nano .env
```

Bootstrap directories:

```bash
bash scripts/bootstrap.sh
```

## Hermes Usage

Keep Hermes state in `~/.hermes`, but keep operational knowledge here in the repo.

Typical pattern:

1. Update files in `context/`, `docs/`, `prompts/`, and `scripts/`
2. Pull the repo on the VPS
3. Ask Hermes to read the relevant files before doing work

Example:

```text
Read /root/HermesBrain/context/prospecting-rules.md and /root/HermesBrain/docs/dataforseo.md, then plan tonight's prospecting run.
```
