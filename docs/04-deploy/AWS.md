# ☁️ Infraestrutura Cloud (AWS / Providers)

## Serviços Utilizados
- **AWS S3:** Bucket seguro para armazenamento dos PDFs enviados pelos clientes e arquivos de template `.xlsx`.
- **ECS (Elastic Container Service) / App Runner ou Vercel:** Hospedagem dos containers da aplicação.
- **Supabase / AWS RDS:** Banco de dados PostgreSQL gerenciado.
- **Upstash / AWS ElastiCache:** Instância Redis serverless para gerenciar a fila do BullMQ.