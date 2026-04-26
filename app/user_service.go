package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

// UserRequest é o JSON enviado ao mock-api POST /user/create.
type UserRequest struct {
	Name    string `json:"name"`
	Message string `json:"message"`
}

// UserService envia um UserRequest ao endpoint configurado.
type UserService struct {
	endpoint   string
	httpClient *http.Client
}

func NewUserService(endpoint string) *UserService {
	return &UserService{
		endpoint:   endpoint,
		httpClient: &http.Client{},
	}
}

func (s *UserService) CreateUser(p Payload) error {
	body := UserRequest{
		Name:    p.Name,
		Message: p.Message,
	}

	data, err := json.Marshal(body)
	if err != nil {
		return fmt.Errorf("failed to marshal user request: %w", err)
	}

	resp, err := s.httpClient.Post(s.endpoint, "application/json", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("failed to call user API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("user API returned unexpected status: %d", resp.StatusCode)
	}
	fmt.Printf("Usuario cadastrado com sucesso. Status Code: %d\n", resp.StatusCode)

	return nil
}
