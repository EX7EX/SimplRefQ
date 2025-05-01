# API Reference

## Authentication

All API requests require authentication using Telegram OAuth or wallet signatures.

### Headers
```
Authorization: Bearer <token>
X-Wallet-Signature: <signature>
```

## Endpoints

### User Management

#### GET /api/users/{user_id}
Retrieve user profile and balance information.

**Response**:
```json
{
  "user_id": "string",
  "username": "string",
  "balance": "number",
  "wallet": "string",
  "rank": "number",
  "referrals": "number",
  "tasks_completed": ["string"]
}
```

#### POST /api/users/{user_id}/update
Update user information.

**Request Body**:
```json
{
  "balance": "number",
  "wallet": "string",
  "tasks_completed": ["string"]
}
```

### Trading Operations

#### POST /api/trade/execute
Execute a trade order.

**Request Body**:
```json
{
  "pair": "string",
  "side": "buy|sell",
  "type": "market|limit",
  "amount": "number",
  "price": "number"
}
```

#### GET /api/trade/orders
Retrieve user's open orders.

**Response**:
```json
{
  "orders": [
    {
      "id": "string",
      "pair": "string",
      "side": "string",
      "type": "string",
      "amount": "number",
      "price": "number",
      "status": "string"
    }
  ]
}
```

### Points System

#### POST /api/points/claim
Claim daily rewards or task completion points.

**Request Body**:
```json
{
  "type": "daily|task",
  "task_id": "string"
}
```

#### GET /api/points/balance
Get user's points balance.

**Response**:
```json
{
  "balance": "number",
  "daily_claimed": "boolean",
  "next_claim_time": "timestamp"
}
```

### AI Services

#### POST /api/ai/signals
Request trading signals.

**Request Body**:
```json
{
  "pair": "string",
  "timeframe": "string",
  "indicators": ["string"]
}
```

**Response**:
```json
{
  "signals": [
    {
      "type": "string",
      "confidence": "number",
      "price_target": "number",
      "timeframe": "string"
    }
  ]
}
```

### Referral System

#### POST /api/referrals/create
Generate a referral link.

**Response**:
```json
{
  "referral_link": "string",
  "code": "string"
}
```

#### GET /api/referrals/stats
Get referral statistics.

**Response**:
```json
{
  "total_referrals": "number",
  "active_referrals": "number",
  "rewards_earned": "number"
}
```

## WebSocket API

### Connection
```
wss://api.simplrefq.com/ws
```

### Events

#### Market Data
```json
{
  "event": "market_data",
  "data": {
    "pair": "string",
    "price": "number",
    "volume": "number",
    "timestamp": "number"
  }
}
```

#### Order Updates
```json
{
  "event": "order_update",
  "data": {
    "order_id": "string",
    "status": "string",
    "filled": "number",
    "remaining": "number"
  }
}
```

## Error Handling

All API errors follow this format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object"
  }
}
```

### Common Error Codes
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

- API requests are limited to 100 requests per minute per IP
- WebSocket connections are limited to 5 per user
- Trading operations are limited based on user tier

## Versioning

API version is specified in the URL:
```
/api/v1/endpoint
```

## Webhook Events

### Order Filled
```json
{
  "event": "order_filled",
  "data": {
    "order_id": "string",
    "pair": "string",
    "amount": "number",
    "price": "number"
  }
}
```

### Points Awarded
```json
{
  "event": "points_awarded",
  "data": {
    "user_id": "string",
    "amount": "number",
    "reason": "string"
  }
}
``` 