# PeakPick Identity Service

Identity Service là microservice quản lý tài khoản demo, cửa hàng, vai trò và token đăng nhập.

## Database Riêng

Service này sở hữu database `peakpick_identity` với các bảng:

- `stores`
- `identity_users`

## Trách Nhiệm

- Đăng nhập bằng tài khoản demo.
- Cấp bearer token.
- Trả thông tin người dùng hiện tại.
- Không xử lý đơn hàng, sản phẩm hoặc slot.

## Chạy Local

```bash
pip install -r requirements.txt
uvicorn services.identity_service.main:app --reload --port 8008
```
