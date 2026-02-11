# NovaPay Coding Standards

*Last updated: October 2024*
*Owner: Developer Experience Team (`#team-devex`)*

## General Principles

1. **Readability over cleverness** — Code is read far more than it's written. Optimize for the reader.
2. **Consistency over preference** — Follow the established patterns in the codebase, even if you'd do it differently.
3. **Test what matters** — We aim for 80%+ code coverage, but prioritize testing complex business logic over boilerplate.
4. **Fail fast, fail loud** — Return errors early, log them with context, and don't swallow exceptions.

## Language-Specific Standards

### Go (Payments API, Payments Core, Auth Service)

- Follow the official [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- Use `golangci-lint` with our shared config (`.golangci.yml` in the monorepo root)
- Error handling: Always wrap errors with context using `fmt.Errorf("doing X: %w", err)`
- Naming: Use short, descriptive variable names. Avoid single-letter names outside of loop indices.
- Concurrency: Prefer channels over mutexes. Always use `context.Context` for cancellation.
- Logging: Use `slog` (structured logging). Include `request_id` and `merchant_id` in all log entries.

```go
// Good
func (s *PaymentService) ProcessPayment(ctx context.Context, req *PaymentRequest) (*Payment, error) {
    logger := slog.With("merchant_id", req.MerchantID, "request_id", middleware.RequestID(ctx))
    logger.Info("processing payment", "amount", req.Amount)
    // ...
}
```

### Python (Users API, Notifications Service, Data Pipelines)

- Follow PEP 8 with a line length of 100 characters
- Use `ruff` for linting and formatting (config in `pyproject.toml`)
- Type hints are **required** for all function signatures
- Use `pydantic` for data validation and serialization
- Async: Use `async/await` consistently. Don't mix sync and async database calls.
- Logging: Use `structlog` with JSON output.

```python
# Good
async def get_merchant(self, merchant_id: str) -> Merchant:
    logger = structlog.get_logger().bind(merchant_id=merchant_id)
    merchant = await self.db.fetch_one(
        "SELECT * FROM merchants WHERE id = :id", {"id": merchant_id}
    )
    if not merchant:
        logger.warning("merchant_not_found")
        raise MerchantNotFoundError(merchant_id)
    return Merchant(**merchant)
```

### TypeScript (Dashboard, Admin Panel, SDKs)

- Use TypeScript strict mode (`"strict": true` in `tsconfig.json`)
- Use `eslint` with our shared config (`@novapay/eslint-config`)
- Prefer `interface` over `type` for object shapes
- Use `zod` for runtime validation of external data
- React: Use functional components with hooks. No class components.
- State management: Use React Query for server state, Zustand for client state.

## API Standards

See the [API Design Guidelines](./api-design-guidelines.md) for API-specific standards.

## Database Standards

- All tables must have `id` (UUID), `created_at`, and `updated_at` columns
- Use `snake_case` for table and column names
- Write migrations using the `novapay db:migration:create` CLI command
- Migrations must be **backward-compatible** (no column drops, renames, or type changes in a single deploy)
- Always add an index for columns used in `WHERE` clauses
- Use database-level constraints (NOT NULL, CHECK, FOREIGN KEY) — don't rely on application-level validation alone

## Testing Standards

- Unit tests: Required for all business logic. Use table-driven tests in Go.
- Integration tests: Required for API endpoints and database interactions. Use testcontainers for database tests.
- E2E tests: Maintained by QA team for critical user flows. Run in staging before production deploys.
- Test naming: `Test<Function>_<Scenario>_<ExpectedBehavior>` (Go) or `test_<function>_<scenario>` (Python)

## Git Standards

- Branch naming: `<team>/<ticket>-<short-description>` (e.g., `payments/PAY-1234-fix-refund-race`)
- Commit messages: Use conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Squash merges to `main` (keeps history clean)
