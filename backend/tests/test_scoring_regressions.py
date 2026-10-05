"""Score inflation regressions, including real production transcript examples."""
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services import ai_scoring

FIXTURES = json.loads((Path(__file__).parent / 'fixtures/scoring_regressions.json').read_text())


class ScoringRegressionTests(unittest.TestCase):
    def test_long_response_cannot_dilute_three_errors_to_perfect_score(self):
        tool = Mock()
        tool.check.return_value = [SimpleNamespace(offset=i*10, error_length=2,
            message='Check grammar.', replacements=['correction']) for i in range(3)]
        text = ' '.join(['word'] * 250)
        with patch.object(ai_scoring, 'get_language_tool', return_value=tool):
            result = ai_scoring.evaluate_answer('', text, 120, 'audio')
        self.assertLessEqual(result['grammar_score'], 7)
        self.assertLessEqual(result['final_score'], 7)
        self.assertIn('Suggested correction', result['feedback'])
        self.assertIn('practice-v2', result['feedback'])

    def test_repeated_detected_errors_decrease_score_for_same_length_and_pace(self):
        tool = Mock()
        text = FIXTURES['good_project']
        scores = []
        with patch.object(ai_scoring, 'get_language_tool', return_value=tool):
            for count in range(7):
                tool.check.return_value = [SimpleNamespace(offset=i*10,error_length=2,
                    message='Agreement.',replacements=[]) for i in range(count)]
                scores.append(ai_scoring.evaluate_answer('', text, 35, 'audio')['final_score'])
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLess(scores[-1], scores[0])
        self.assertLessEqual(scores[1],9)

    def test_obvious_agreement_and_comparative_errors(self):
        for text, expected in [('I does not understand.', 'do'),
                               ('We has finished.', 'have'),
                               ('They was waiting.', 'were'),
                               ('Why he think that?', 'thinks'),
                               ('She have a project.', 'has'),
                               ('This works more better.', 'better')]:
            with self.subTest(text=text):
                issues = ai_scoring.supplemental_grammar_issues(text)
                self.assertEqual(len(issues),1)
                self.assertEqual(issues[0].replacement,expected)

    def test_valid_auxiliary_questions_and_subjunctives_not_flagged(self):
        for text in ['Does he think it will work?', 'Can she have a turn?',
                     'Did they have time?', 'I suggest that she work with us.',
                     'It is essential that he have enough time.', 'If I were you, I would wait.',
                     FIXTURES['good_project'], FIXTURES['good_disagreement']]:
            with self.subTest(text=text):
                self.assertEqual(ai_scoring.supplemental_grammar_issues(text),[])

    def test_language_tool_and_supplement_do_not_double_count_same_error(self):
        text = 'I does not understand.'
        match = SimpleNamespace(offset=2,error_length=4,message='Agreement.',replacements=['do'])
        issues = ai_scoring.collect_grammar_issues(text,[match])
        self.assertEqual(len(issues),1)
        self.assertEqual(issues[0].replacement,'do')

    def test_grammar_bounds_and_no_length_washout(self):
        for count in [1,10,100,10000]:
            for errors in [0,1,3,100]:
                self.assertTrue(0 <= ai_scoring.calculate_grammar_score(errors,count) <= 10)
        self.assertEqual(ai_scoring.calculate_grammar_score(3,100),
                         ai_scoring.calculate_grammar_score(3,10000))
        self.assertEqual(ai_scoring.calculate_grammar_score(0,0),0)


@unittest.skipUnless(os.getenv('RUN_REAL_GRAMMAR')=='1', 'Run explicitly with cached local LanguageTool')
class RealGrammarRegressionTests(unittest.TestCase):
    def test_actual_engine_on_production_transcripts_and_clean_controls(self):
        for topic in ['project','disagreement']:
            good = ai_scoring.evaluate_answer('', FIXTURES['good_'+topic], 35, 'audio')
            bad = ai_scoring.evaluate_answer('', FIXTURES['bad_'+topic],
                                            46 if topic=='project' else 120, 'audio')
            print(topic, json.dumps({'good':good,'bad':bad}), flush=True)
            self.assertGreater(good['grammar_score'],bad['grammar_score'])
            self.assertGreater(good['final_score'],bad['final_score'])
            self.assertGreaterEqual(good['grammar_score'],8)
            self.assertLessEqual(bad['final_score'],7)
            self.assertIn('Suggested correction',bad['feedback'])
