# Rollback Procedure

## Database Rollback

### Automatic Rollback

```bash
# Rollback to previous migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade <revision_id>

# Rollback multiple steps
alembic downgrade -3
```

### Manual Rollback

1. **Stop Application Services**
```bash
docker compose -f docker-compose.prod.yml down
```

2. **Backup Current Database**
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_before_rollback.sql
```

3. **Restore from Backup**
```bash
docker compose -f docker-compose.prod.yml exec -T postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} < backup_file.sql
```

4. **Verify Data Integrity**
```bash
# Check table counts
docker compose -f docker-compose.prod.yml exec postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} -c "SELECT COUNT(*) FROM content_items;"
docker compose -f docker-compose.prod.yml exec postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} -c "SELECT COUNT(*) FROM payments;"
```

5. **Restart Services**
```bash
docker compose -f docker-compose.prod.yml up -d
```

## Application Rollback

### Docker Image Rollback

1. **View Previous Images**
```bash
docker images | grep aifp-aos
```

2. **Tag Previous Version**
```bash
docker tag aifp-aos-api:latest aifp-aos-api:rollback
docker tag aifp-aos-worker:latest aifp-aos-worker:rollback
docker tag aifp-aos-dashboard:latest aifp-aos-dashboard:rollback
```

3. **Update docker-compose.prod.yml**
```yaml
api:
  image: aifp-aos-api:rollback
worker:
  image: aifp-aos-worker:rollback
dashboard:
  image: aifp-aos-dashboard:rollback
```

4. **Redeploy**
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Code Rollback

1. **Checkout Previous Commit**
```bash
git log --oneline
git checkout <commit_hash>
```

2. **Rebuild and Deploy**
```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Configuration Rollback

### Environment Variables

1. **Backup Current Configuration**
```bash
cp .env .env.backup
```

2. **Restore Previous Configuration**
```bash
cp .env.backup .env
```

3. **Restart Services**
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Nginx Configuration

1. **Backup Current Configuration**
```bash
cp nginx/nginx.conf nginx/nginx.conf.backup
cp nginx/templates/default.conf.template nginx/templates/default.conf.template.backup
```

2. **Restore Previous Configuration**
```bash
cp nginx/nginx.conf.backup nginx/nginx.conf
cp nginx/templates/default.conf.template.backup nginx/templates/default.conf.template
```

3. **Reload Nginx**
```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## Emergency Rollback

### Full System Rollback

1. **Stop All Services**
```bash
docker compose -f docker-compose.prod.yml down
```

2. **Restore Database from Last Known Good Backup**
```bash
docker compose -f docker-compose.prod.yml exec -T postgres psql -U ${POSTGRES_USER} ${POSTGRES_DB} < last_known_good_backup.sql
```

3. **Rollback Code to Last Known Good Commit**
```bash
git checkout <last_known_good_commit>
docker compose -f docker-compose.prod.yml build
```

4. **Restore Configuration**
```bash
cp .env.last_known_good .env
cp nginx/nginx.conf.last_known_good nginx/nginx.conf
```

5. **Start Services**
```bash
docker compose -f docker-compose.prod.yml up -d
```

6. **Verify System Health**
```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# Check API health
curl https://your-domain.com/health

# Check database connectivity
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U ${POSTGRES_USER}
```

## Rollback Verification Checklist

- [ ] Database restored successfully
- [ ] All tables have expected row counts
- [ ] API returns healthy status
- [ ] Dashboard loads correctly
- [ ] Payment processing functional
- [ ] Background worker processing tasks
- [ ] No error logs in any service
- [ ] SSL certificates valid
- [ ] Rate limiting active
- [ ] Authentication and authorization working

## Rollback Communication

1. **Notify Stakeholders**
   - Development team
   - Operations team
   - Product owners
   - Users (if production rollback)

2. **Document Incident**
   - Time of rollback
   - Reason for rollback
   - Changes rolled back
   - Verification steps taken
   - Preventive measures for future

3. **Post-Rollback Review**
   - Root cause analysis
   - Process improvements
   - Updated rollback procedures
   - Team training if needed
