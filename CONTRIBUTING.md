# Como Contribuir

Obrigado pelo seu interesse em contribuir com o **DocuSmart**!

Este projeto é um micro-pipeline serverless focado em análise de documentos via Amazon Strands Agents e AWS. 

## O que você pode fazer
1. **Reportar Bugs:** Abra uma *Issue* detalhando o problema, como reproduzi-lo e informações do seu ambiente.
2. **Sugerir Melhorias:** Adicione sugestões na aba de *Issues*. Novas ferramentas para os Agentes Strands são sempre bem-vindas!
3. **Enviar Código:** Caso resolva algum bug ou adicione uma feature.

## Passos para submeter código (Pull Request)

1. Faça um **Fork** do repositório.
2. Crie uma branch para a sua feature (`git checkout -b feature/minha-feature`).
3. Instale as dependências locais:
   ```bash
   pip install -r requirements.txt
   ```
4. Escreva testes para a nova funcionalidade na pasta `tests/`.
5. Rode os testes localmente usando `pytest`.
6. Faça o commit das suas alterações (`git commit -m 'feat: adiciona nova funcionalidade X'`).
7. Faça um push para a branch (`git push origin feature/minha-feature`).
8. Abra o Pull Request!

## Estilo de Código
- Usamos Python 3.12.
- Siga a PEP 8 sempre que possível.
- As Lambdas buscam manter-se independentes, garantindo fácil implantação manual ou via SAM.

Agradeço imensamente!
