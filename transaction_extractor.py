import json
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionExtractor:
    """
    Service for extracting transaction details from statement text using Groq LLM
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("No GROQ_API_KEY provided for transaction extraction")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
    
    def extract_transactions(self, statement_text: str, statement_id: str) -> Dict[str, Any]:
        """
        Extract transaction details from statement text using Groq LLM
        
        Args:
            statement_text: The extracted text from the statement
            statement_id: The statement ID for tracking
            
        Returns:
            Dictionary containing extracted transactions and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "Groq API client not initialized. Check GROQ_API_KEY.",
                "transactions": []
            }
        
        try:
            # Create the prompt for transaction extraction
            prompt = self._create_extraction_prompt(statement_text)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",  # Using Llama 3 8B model
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            raw_response = response.choices[0].message.content
            logger.info(f"Raw LLM response for statement {statement_id}: {raw_response[:500]}...")
            
            # Parse JSON response
            extracted_data = json.loads(raw_response)
            
            # Process and validate the extracted transactions
            processed_transactions = self._process_transactions(
                extracted_data.get("transactions", []),
                statement_id,
                raw_response
            )
            
            return {
                "success": True,
                "total_transactions": len(processed_transactions),
                "transactions": processed_transactions,
                "raw_response": raw_response,
                "confidence_score": extracted_data.get("confidence", 0.8)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for statement {statement_id}: {e}")
            return {
                "success": False,
                "error": f"Invalid JSON response from LLM: {str(e)}",
                "transactions": [],
                "raw_response": raw_response if 'raw_response' in locals() else None
            }
        except Exception as e:
            logger.error(f"Transaction extraction failed for statement {statement_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "transactions": []
            }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for transaction extraction"""
        return """You are an expert financial document processor specializing in extracting transaction details from bank statements, credit card statements, and other financial documents.

Your task is to extract individual transactions from the provided statement text and return them in a structured JSON format.

For each transaction, extract the following information when available:
- transaction_date: Date of the transaction (YYYY-MM-DD format)
- description: Full description of the transaction
- amount: Transaction amount (positive for credits, negative for debits)
- transaction_type: Type (debit, credit, withdrawal, deposit, etc.)
- balance: Account balance after transaction (if available)
- reference_number: Any reference/check number
- category: General category (food, gas, shopping, etc.)

IMPORTANT FORMATTING RULES:
1. Return ONLY valid JSON
2. Use null for missing information
3. Format dates as YYYY-MM-DD strings
4. Format amounts as numbers (use negative for debits/withdrawals)
5. Keep descriptions concise but complete
6. Assign reasonable categories based on merchant names

Response format:
{
  "transactions": [
    {
      "transaction_date": "2024-01-15",
      "description": "WALMART SUPERCENTER",
      "amount": -125.50,
      "transaction_type": "debit",
      "balance": 1875.32,
      "reference_number": "4567",
      "category": "shopping"
    }
  ],
  "confidence": 0.95,
  "total_found": 1
}"""
    
    def _create_extraction_prompt(self, statement_text: str) -> str:
        """Create the user prompt with statement text"""
        # Truncate very long texts to avoid token limits
        max_chars = 10000
        if len(statement_text) > max_chars:
            statement_text = statement_text[:max_chars] + "\n\n[TEXT TRUNCATED]"
        
        return f"""Please extract all transaction details from the following financial statement text:

{statement_text}

Extract each transaction with all available details and return as JSON following the specified format."""
    
    def _process_transactions(self, transactions: List[Dict], statement_id: str, raw_response: str) -> List[Dict]:
        """
        Process and validate extracted transactions
        
        Args:
            transactions: Raw transactions from LLM
            statement_id: Statement ID for tracking
            raw_response: Raw LLM response for storage
            
        Returns:
            List of processed transaction dictionaries
        """
        processed = []
        
        for i, transaction in enumerate(transactions):
            try:
                processed_transaction = {
                    "statement_id": statement_id,
                    "transaction_date": self._parse_date(transaction.get("transaction_date")),
                    "description": self._clean_description(transaction.get("description")),
                    "amount": self._parse_amount(transaction.get("amount")),
                    "transaction_type": self._normalize_transaction_type(transaction.get("transaction_type")),
                    "balance": self._parse_amount(transaction.get("balance")),
                    "reference_number": self._clean_string(transaction.get("reference_number")),
                    "category": self._normalize_category(transaction.get("category")),
                    "extraction_source": "llm",  # Mark as LLM extracted
                    "confidence_score": transaction.get("confidence", 0.8),
                    "llm_raw_response": raw_response,
                    "processing_completed": True
                }
                
                processed.append(processed_transaction)
                
            except Exception as e:
                logger.warning(f"Failed to process transaction {i} for statement {statement_id}: {e}")
                # Store failed transaction with error info
                processed.append({
                    "statement_id": statement_id,
                    "description": f"Failed to process transaction {i}: {str(e)}",
                    "processing_completed": False,
                    "processing_error": str(e),
                    "llm_raw_response": raw_response
                })
        
        return processed
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None
    
    def _parse_amount(self, amount: Any) -> Optional[Decimal]:
        """Parse amount to Decimal"""
        if amount is None:
            return None
        
        try:
            # Handle string amounts with currency symbols
            if isinstance(amount, str):
                # Remove common currency symbols and spaces
                cleaned = amount.replace("$", "").replace(",", "").replace(" ", "")
                return Decimal(cleaned)
            else:
                return Decimal(str(amount))
        except Exception:
            return None
    
    def _clean_description(self, description: Any) -> Optional[str]:
        """Clean and normalize description"""
        if not description:
            return None
        
        return str(description).strip()[:500]  # Limit length
    
    def _clean_string(self, value: Any) -> Optional[str]:
        """Clean string value"""
        if not value:
            return None
        
        return str(value).strip()[:255]  # Limit length
    
    def _normalize_transaction_type(self, trans_type: Any) -> Optional[str]:
        """Normalize transaction type"""
        if not trans_type:
            return None
        
        trans_type = str(trans_type).lower().strip()
        
        # Map common variations
        type_mapping = {
            "debit": "debit",
            "credit": "credit",
            "withdrawal": "withdrawal",
            "deposit": "deposit",
            "purchase": "purchase",
            "payment": "payment",
            "transfer": "transfer",
            "fee": "fee"
        }
        
        return type_mapping.get(trans_type, trans_type)
    
    def _normalize_category(self, category: Any) -> Optional[str]:
        """Normalize transaction category"""
        if not category:
            return None
        
        category = str(category).lower().strip()
        
        # Map common categories
        category_mapping = {
            "grocery": "groceries",
            "groceries": "groceries",
            "food": "food",
            "restaurant": "food",
            "dining": "food",
            "gas": "fuel",
            "fuel": "fuel",
            "shopping": "shopping",
            "retail": "shopping",
            "entertainment": "entertainment",
            "medical": "healthcare",
            "healthcare": "healthcare",
            "utility": "utilities",
            "utilities": "utilities",
            "transfer": "transfer",
            "payment": "payment",
            "fee": "fees",
            "fees": "fees"
        }
        
        return category_mapping.get(category, category)