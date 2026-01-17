
import os
import time
from datetime import datetime
from queue import Queue
from threading import Event

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from tool_calling import get_tools
from notifier import notify
from utils import compute_latency
from logger import logger
from config import Config

def handle_speech_input(
    audio_queue: Queue, 
    pause_listener_event: Event, 
    frame_request_queue: Queue, 
    frame_response_queue: Queue
):
    """
    Processes recognized speech using an LLM agent.
    """
    if not Config.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set. Speech handler cannot function.")
        return

    # Initialize generic tools
    tools = get_tools(frame_request_queue, frame_response_queue)

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0, 
        api_key=Config.OPENAI_API_KEY
    )

    # Create Prompt
    # We remove the "speak before" instruction as the tool handles its own notification.
    # We explicitly tell it to use tools for item/visitor queries.
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful room agent assistant. You help manage visitor logs and item storage.\n"
            "Use the provided tools for ANY query related to finding items, storing items, or visitor logs.\n"
            "After a tool like 'RetrieveItemLocation' or 'ListStoredItems' finishes, the user has ALREADY reviewed the items visually.\n"
            "CRITICAL: Do NOT list the items, their locations, or IDs again in your spoken response. "
            "Just provide a very brief, friendly wrap-up (e.g. 'I've updated the records.' or 'Hope those images helped!').\n"
            "Current date and time: {current_datetime}"
        )),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create Agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # Create Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True, # Keep verbose for inner reasoning logs, or set to False to clean up
        handle_parsing_errors=True,
        max_iterations=3,
        return_intermediate_steps=True
    )
    
    logger.info("Speech handler initialized and ready.")

    while True:   
        try:
            text = audio_queue.get()
            if not text:
                continue
                
            # Pause listener while processing
            pause_listener_event.set()
            
            start = time.time()
            logger.info(f"Processing query: {text}")
            
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                # Invoke Agent
                result = agent_executor.invoke({
                    "input": text,
                    "current_datetime": current_datetime
                })
                response = result["output"]
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                response = "I'm sorry, I ran into an error processing your request."
            
            end = time.time()
            compute_latency(start, end, "Agent Processing")

            # Output response (Audio + Log)
            logger.info(f"Agent response: {response}")
            notify(response)
            
            # Resume listener
            pause_listener_event.clear()
            
        except Exception as e:
            logger.error(f"Unexpected error in speech handler: {e}")
            pause_listener_event.clear()
