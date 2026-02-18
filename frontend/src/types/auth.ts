export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  clinic_id: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  clinic_name: string;
  clinic_slug: string;
  email: string;
  password: string;
  name: string;
}
