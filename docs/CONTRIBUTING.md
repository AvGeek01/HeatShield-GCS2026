# Contributing

- Keep one owner per folder: R owns `/heatcore` and `/data`; S owns `/web`; K owns `/backend`, `/firmware`, and `/docs`.
- Prefix documentation files with the author's initial (for example, `K_notes.md`).
- Start commit messages with the author's initial and a colon: `R:`, `S:`, or `K:`.
- Before pushing, always run `git pull --rebase origin main`, then `git push origin main`.
- Never force-push.
- Never commit secrets, personal data, or large files. Keep credentials out of git and store raw interviews, signed forms, survey exports, and videos in the ignored `private/` folder; back them up outside git.