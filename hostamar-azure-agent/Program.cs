using Azure.AI.OpenAI;
using Azure.Identity;
using System.ClientModel;
using OpenAI.Assistants;
using System;
using System.Threading.Tasks;
using System.Linq;
using System.Collections.Generic;

#pragma warning disable OPENAI001

namespace HostamarAzureAgent
{
    class Program
    {
        // Configuration
        const string endpoint = "https://hostamar-resource.openai.azure.com/"; 
        const string agentName = "1hostamar";
        const string modelDeployment = "gpt-4o"; // Ensure this deployment exists in your Azure AI Studio

        static async Task Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.WriteLine("==========================================");
            Console.WriteLine("   HOSTAMAR AZURE AI AGENT: 1hostamar     ");
            Console.WriteLine("   (Azure OpenAI Assistants API)          ");
            Console.WriteLine("==========================================");

            try
            {
                // 1. Authenticate
                Console.WriteLine("--> Authenticating...");
                var credential = new DefaultAzureCredential();
                var client = new AzureOpenAIClient(new Uri(endpoint), credential);
                var assistantClient = client.GetAssistantClient();

                // 2. Find Agent (Assistant)
                Console.WriteLine($"--> Locating Agent: '{agentName}'...");
                Assistant assistant = null;
                
                // List assistants to find our named agent
                // Note: Pagination might be needed for many assistants
                await foreach (var item in assistantClient.GetAssistantsAsync())
                {
                    if (item.Name == agentName)
                    {
                        assistant = item;
                        Console.WriteLine($"✅ Found Agent: {assistant.Name} ({assistant.Id})");
                        break;
                    }
                }

                if (assistant == null)
                {
                    Console.WriteLine("⚠️  Agent not found. Creating a new one...");
                    assistant = await assistantClient.CreateAssistantAsync(modelDeployment, new AssistantCreationOptions
                    {
                        Name = agentName,
                        Instructions = "You are a specialized assistant for Hostamar infrastructure."
                    });
                    Console.WriteLine($"✅ Created Agent: {assistant.Id}");
                }

                // 3. Create Thread
                Console.WriteLine("--> Creating conversation thread...");
                var thread = await assistantClient.CreateThreadAsync();
                Console.WriteLine($"✅ Thread Active: {thread.Value.Id}");

                // 4. Interaction Loop
                Console.WriteLine("\nAgent Ready. Type your prompt below (or 'exit' to quit).");
                Console.WriteLine("-------------------------------------------------------");

                while (true)
                {
                    Console.Write("\nYou: ");
                    var input = Console.ReadLine();
                    if (string.IsNullOrWhiteSpace(input)) continue;
                    if (input.ToLower() == "exit") break;

                    try 
                    {
                        // A. Add Message
                        await assistantClient.CreateMessageAsync(thread.Value.Id, MessageRole.User, new[] { MessageContent.FromText(input) });

                        // B. Run Agent
                        Console.Write("Agent: Thinking...");
                        var run = await assistantClient.CreateRunAsync(thread.Value.Id, assistant.Id);

                        // C. Poll for completion
                        while (run.Value.Status == RunStatus.Queued || run.Value.Status == RunStatus.InProgress)
                        {
                            await Task.Delay(500);
                            run = await assistantClient.GetRunAsync(thread.Value.Id, run.Value.Id);
                            Console.Write(".");
                        }

                        if (run.Value.Status == RunStatus.Completed)
                        {
                            // D. Fetch Response
                            // Get the list of messages in the thread
                            var messages = assistantClient.GetMessagesAsync(thread.Value.Id);
                            
                            // We need to find the FIRST message that is role=assistant and run_id matches
                            await foreach (var msg in messages)
                            {
                                if (msg.Role == MessageRole.Assistant && msg.RunId == run.Value.Id)
                                {
                                    foreach (var contentItem in msg.Content)
                                    {
                                        if (!string.IsNullOrEmpty(contentItem.Text))
                                        {
                                            Console.Write($"\rAgent: {contentItem.Text}\n");
                                        }
                                    }
                                    break;
                                }
                            }
                        }
                        else
                        {
                            Console.WriteLine($"\n❌ Run Status: {run.Value.Status}");
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"\n❌ Turn Error: {ex.Message}");
                    }
                }

            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ Fatal Error: {ex.Message}");
                Console.WriteLine("Note: Ensure endpoint is correct and you have 'Cognitive Services OpenAI User' role.");
            }
        }
    }
}