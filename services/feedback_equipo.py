"""
Team feedback implementation.
"""

from typing import List
from datetime import datetime
import json
import logging
from models import EvaluationDTO, FeedbackDTO
from core.llm import LLMFactory, LLMProvider
from models.submission import SubmissionDTO
from .feedback_prompts import FeedbackPrompts

# Configure logger
logger = logging.getLogger(__name__)


class FeedbackEquipo():
    """
    Feedback maker for team-level feedback.
    
    Team feedback typically provides peer-to-peer insights,
    collaboration assessment, and team dynamics analysis.
    """
    
    @property
    def feedback_type(self) -> str:
        """Return the feedback type identifier."""
        return "equipo"
    
    async def make_feedback(self, submission: SubmissionDTO, evaluations: List[EvaluationDTO]) -> FeedbackDTO:
        """
        Generate team feedback based on evaluations.
        
        Args:
            evaluations: List of evaluations for a submission
            
        Returns:
            FeedbackDTO with team feedback
        """
        logger.info(f"Starting team feedback generation for submission {submission.id}, team: {submission.team_name}")
        logger.debug(f"Received {len(evaluations)} evaluations")
    

        logger.info("Generating team strengths...")
        strengths = await self._generate_team_strengths(submission, evaluations)
        logger.debug(f"Strengths generated: {len(strengths)} characters")
        
        logger.info("Generating team improvements...")
        improvements = await self._generate_team_improvements(submission, evaluations)
        logger.debug(f"Improvements generated: {len(improvements)} characters")
        
        logger.info("Generating final team feedback content...")
        content = await self._generate_team_feedback(strengths, improvements, submission, evaluations)
        logger.debug(f"Final content generated: {len(content)} characters")
        
        # Create feedback DTO
        feedback = FeedbackDTO(
            submission_id=submission.id,
            feedback_type=self.feedback_type,
            content=content,
            feedback_date=datetime.now(),
            strengths=strengths,
            improvements=improvements,
            team_name=submission.team_name,
            assignment_title=submission.assignment_title
        )
        
        logger.info(f"Team feedback generation completed successfully for submission {submission.id}")
        return feedback

    async def _generate_team_feedback(self, strengths: str, improvements: str, submission: SubmissionDTO, evaluations: List[EvaluationDTO]) -> str:
        """
        Generate the actual feedback content for team using LLM.
        
        Args:
            evaluations: List of evaluations
            
        Returns:
            Generated feedback content
        """
        logger.debug("Preparing prompt for team general feedback")
        
        criteria_json = self._generate_criteria_json(evaluations)
        evaluation_types = self._get_evaluation_types(evaluations)
        
        logger.debug(f"Criteria JSON length: {len(criteria_json)}")
        logger.debug(f"Evaluation types: {evaluation_types}")

        prompt = FeedbackPrompts.TEAM_GENERAL_FEEDBACK_PROMPT.format(
            team_name=submission.team_name,
            assignment_title=submission.assignment_title,
            count=len(evaluations),
            criteria_json=criteria_json,
            evaluation_types=evaluation_types,
            strengths=strengths,
            improvements=improvements
        )

        logger.debug(f"Prompt prepared, length: {len(prompt)} characters")

        try:
            logger.debug("Creating LLM instance...")
            llm = LLMFactory.create_llm(
                provider=LLMProvider.DEEPSEEK,
                temperature=0.3
            )
            logger.debug("Invoking LLM for team general feedback...")
            response = await llm.ainvoke(prompt)
            logger.info("LLM response received successfully for team general feedback")
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM for team general feedback: {str(e)}")
            return "Error conectándose al LLM"

    async def _generate_team_strengths(self, submission: SubmissionDTO, evaluations: List[EvaluationDTO]) -> str:
        """
        Generate team strengths using LLM.
        
        Args:
            evaluation_data: Prepared evaluation summary
            
        Returns:
            Generated strengths text
        """
        logger.debug("Preparing prompt for team strengths")
        
        criteria_json = self._generate_criteria_json(evaluations)
        evaluation_types = self._get_evaluation_types(evaluations)
        
        prompt = FeedbackPrompts.get_strengths_prompt(
            team_name=submission.team_name,
            assignment_title=submission.assignment_title,
            count=len(evaluations),
            criteria_json=criteria_json,
            evaluation_types=evaluation_types
        )

        logger.debug(f"Strengths prompt prepared, length: {len(prompt)} characters")

        try:
            logger.debug("Creating LLM instance for strengths...")
            llm = LLMFactory.create_llm(
                provider=LLMProvider.DEEPSEEK,
                temperature=0.3
            )
            logger.debug("Invoking LLM for team strengths...")
            response = await llm.ainvoke(prompt)
            logger.info("LLM response received successfully for team strengths")
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM for team strengths: {str(e)}")
            return "Error conectándose al LLM"
    
    async def _generate_team_improvements(self, submission: SubmissionDTO, evaluations: List[EvaluationDTO]) -> str:
        """
        Generate team improvement areas using LLM.
        
        Args:
            evaluation_data: Prepared evaluation summary
            
        Returns:
            Generated improvements text
        """
        logger.debug("Preparing prompt for team improvements")
        
        criteria_json = self._generate_criteria_json(evaluations)
        evaluation_types = self._get_evaluation_types(evaluations)
        
        prompt = FeedbackPrompts.get_improvements_prompt(
            team_name=submission.team_name,
            assignment_title=submission.assignment_title,
            count=len(evaluations),
            criteria_json=criteria_json,
            evaluation_types=evaluation_types
        )

        logger.debug(f"Improvements prompt prepared, length: {len(prompt)} characters")

        try:
            logger.debug("Creating LLM instance for improvements...")
            llm = LLMFactory.create_llm(
                provider=LLMProvider.DEEPSEEK,
                temperature=0.3
            )
            logger.debug("Invoking LLM for team improvements...")
            response = await llm.ainvoke(prompt)
            logger.info("LLM response received successfully for team improvements")
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM for team improvements: {str(e)}")
            return "Error conectándose al LLM"
    
    def _generate_criteria_json(self, evaluations: List[EvaluationDTO]) -> str:
        """
        Generate a concatenated string from criteria_json fields of evaluations.
        
        Args:
            evaluations: List of evaluations
            
        Returns:
            Concatenated criteria_json string, limited in length
        """
        logger.debug(f"Processing criteria_json for {len(evaluations)} evaluations")
        
        criteria_list = []
        for evaluation in evaluations:
            if hasattr(evaluation, 'criteria_json') and evaluation.criteria_json:
                criteria_list.append(str(evaluation.criteria_json))
        
        concatenated = " ".join(criteria_list)
        
        # Limit length to avoid excessively long messages (5000 characters max)
        max_length = 5000
        if len(concatenated) > max_length:
            logger.debug(f"Criteria JSON truncated from {len(concatenated)} to {max_length} characters")
            concatenated = concatenated[:max_length] + "..."
        
        logger.debug(f"Final criteria JSON length: {len(concatenated)} characters")
        return concatenated
    
    def _get_evaluation_types(self, evaluations: List[EvaluationDTO]) -> str:
        """
        Get comma-separated evaluation types from evaluations.
        
        Args:
            evaluations: List of evaluations
            
        Returns:
            Comma-separated evaluation types string
        """
        logger.debug(f"Extracting evaluation types from {len(evaluations)} evaluations")
        
        evaluation_types = []
        for evaluation in evaluations:
            if hasattr(evaluation, 'evaluation_type') and evaluation.evaluation_type:
                evaluation_types.append(str(evaluation.evaluation_type))
        
        result = ", ".join(evaluation_types)
        logger.debug(f"Evaluation types found: {result}")
        return result
    