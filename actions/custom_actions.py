from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from neo4j import GraphDatabase

class QueryDiseasesAction(Action):
    def __init__(self):
        super().__init__()
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "action123"))

    def name(self) -> Text:
        return "action_query_diseases" 

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Extract symptoms from the user's input
        symptoms = tracker.latest_message.get('entities', [])
        symptom_names = [symptom['value'] for symptom in symptoms if symptom['entity'] == 'symptom']

        if not symptom_names:
            dispatcher.utter_message(text="I couldn't detect any symptoms in your message.")
            return []


        # Query the knowledge graph for diseases associated with the symptoms
        diseases = self.query_diseases(symptom_names)

        # Respond with the retrieved diseases
        if diseases:
            dispatcher.utter_message(text=f"The possible diseases based on your symptoms are: {', '.join(diseases)}")
        else:
            dispatcher.utter_message(text="I couldn't find any diseases associated with the symptoms you mentioned.")

        return []

    def query_diseases(self, symptoms: List[Text]) -> List[Text]:
        try:
        # Connect to the Neo4j database and execute the query
          with self.driver.session() as session:
            # Constructing the Cypher query dynamically to match diseases associated with all provided symptoms
            query = (
                "MATCH (d:Disease)-[:hasSymptom]->(s:Symptom) "
                "WHERE s.name IN $symptoms "
                "WITH d, COUNT(DISTINCT s) AS num_symptoms "
                "WHERE num_symptoms = $num_symptoms "
                "RETURN DISTINCT d.name"
            )
            # Parameters to be passed into the query
            params = {"symptoms": symptoms, "num_symptoms": len(symptoms)}
            result = session.run(query, **params)
            return [record['d.name'] for record in result]
        except Exception as e:
         print(f"Error querying Neo4j database: {e}")
        return []




