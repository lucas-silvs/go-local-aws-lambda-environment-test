// main.go
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"gopkg.in/yaml.v3"
)

// Payload representa o YAML esperado no body de cada mensagem SQS.
// Adicione ou renomeie campos conforme necessário.
type Payload struct {
	Name    string `yaml:"name"`
	Message string `yaml:"message"`
}

func handler(ctx context.Context, sqsEvent events.SQSEvent) error {
	userAPIURL := os.Getenv("USER_API_URL")
	if userAPIURL == "" {
		return fmt.Errorf("USER_API_URL environment variable is not set")
	}
	svc := NewUserService(userAPIURL)

	for _, record := range sqsEvent.Records {
		log.Printf("MessageId: %s", record.MessageId)

		var p Payload
		if err := yaml.Unmarshal([]byte(record.Body), &p); err != nil {
			return fmt.Errorf("failed to parse YAML from message %s: %w", record.MessageId, err)
		}

		log.Printf("Parsed payload — name: %s | message: %s", p.Name, p.Message)

		if err := svc.CreateUser(p); err != nil {
			return fmt.Errorf("CreateUser failed for message %s: %w", record.MessageId, err)
		}

		log.Printf("User created successfully for message %s", record.MessageId)
	}
	return nil
}

func main() {
	lambda.Start(handler)
}