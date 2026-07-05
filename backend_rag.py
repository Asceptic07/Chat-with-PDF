import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.summarize import load_summarize_chain

class RAGHelper:
    def __init__(self):
        self.vector_store = None
        self.chain = None
        self.docs = []
        
        # Initialize Embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # INCREASED INTELLIGENCE: 
        # temperature=0.3 allows for better phrasing/synthesis while keeping facts straight.
        self.llm = ChatOllama(model="llama3.2", temperature=0.3)

    def load_document(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Load PDF
        loader = PyPDFLoader(file_path)
        self.docs = loader.load()

        if not self.docs:
            raise ValueError("PDF is empty or could not be read.")

        # 2. Split Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(self.docs)

        # 3. Create Vector Store
        self.vector_store = FAISS.from_documents(splits, self.embeddings)

        # 4. Create Retrieval Chain
        # INCREASED CONTEXT: k=6 means "Read the top 6 most relevant pages/paragraphs"
        # The default is 4. Increasing this helps it understand broader context.
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 6})
        
        # === THE BRAIN UPGRADE ===
        # We removed the "3 sentences" limit and added reasoning instructions.
        system_prompt = (
            "You are an intelligent document analyst. Your task is to answer the user's question "
            "based strictly on the provided context."
            "\n\n"
            "Guidelines:"
            "\n1. If the answer is explicitly in the text, provide a clear and detailed explanation."
            "\n2. If the answer requires connecting information from different parts of the document, "
            "synthesize the information to form a complete answer."
            "\n3. Do not make up information. If the context does not contain the answer, "
            "simply state: 'I analyzed the document, but I could not find specific information regarding [topic].'"
            "\n\n"
            "Context:"
            "\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        self.chain = create_retrieval_chain(retriever, question_answer_chain)

    def get_document_overview(self):
        """
        Generates a summary of the uploaded document using the first few pages.
        """
        if not self.docs:
            return "No document loaded to summarize."

        # Take first 5 pages for a better overview
        preview_docs = self.docs[:5]
        
        summary_chain = load_summarize_chain(self.llm, chain_type="stuff")
        summary_response = summary_chain.invoke({"input_documents": preview_docs})
        return summary_response["output_text"]

    def ask_question(self, query):
        if not self.chain:
            return "Please upload a PDF document first."
        
        response = self.chain.invoke({"input": query})
        return str(response["answer"])