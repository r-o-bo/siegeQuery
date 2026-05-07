import json
import boto3

# initializing the sagemaker and s3 clients
sagemaker_client = boto3.client("sagemaker-runtime")
s3_client = boto3.client("s3")


def lambda_handler(event, context):
        # get user input 
        user_input = event.get("user_input","").strip()

        try:
            # fetch data from s3
            s3_response = s3_client.get_object(Bucket="rainbow-six",Key="rainbow_op.json")
            data = json.loads(s3_response["Body"].read().decode("utf-8"))

            # check if user is talking about the data
            if any(keyword in user_input.lower() for keyword in ["operator", "siege", "rainbow six", "r6", "attacker",
            "defender", "ability", "loadout", "speed", "armor"]):
               prompt = f"""
                You are an expert in Tom Clancy's Rainbow Six Siege.

                Use ONLY the reference data below to answer the user's question.
                If the answer is not in the reference data, say you don't know.

                Reference Data:
                {json.dumps(data, indent=2)}

                User Question:
                {user_input}

                Answer:
                """ 
            else:
                prompt = f"""
                User: {user_input}

                You are a professional video game expert.

                Answer the user's question clearly and in a beginner-friendly way.
                Use examples if helpful.
            
                """
            
            # call the sagemaker endpoint to invoke LLM with the prompt
            print("Prompt: {}".format(prompt))
            response = sagemaker_client.invoke_endpoint(
                EndpointName="meta-textgeneration-llama-2-7b",
                ContentType="application/json",
                Body = json.dumps({"inputs" : prompt,
                                "parameters" : {"temperature" : 0.2, "max_new_tokens": 200}}),
            )

            # decode model response
            raw_response = response["Body"].read().decode("utf-8")
            print("Raw SageMaker response", raw_response)
            response_body = json.loads(raw_response)

            if isinstance(response_body, list) and len(response_body) > 0:
                response_body = response_body[0]

            generated_text = response_body.get("generated_text","No response generated.")

            return {
                "statusCode" : 200,
                "body" : json.dumps({"response" : generated_text})
            }

        except Exception as e:
            print("Lamdda error", str(e))
            return {"statusCode" : 500,
                    "body" : json.dumps({"error" : str(e)})
            }